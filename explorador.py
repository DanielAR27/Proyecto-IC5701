#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explorador (Explorador) para el lenguaje C-rvicio Militar
Texto -> Regex -> Lista de tokens
Autoría: Equipo (Daniel, José, Luis, Oscar, Sebastián)

Notas:
- Comentarios permitidos: // ... y /* ... */
- Preferencia: comentarios sin emojis ni adornos.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Any, Iterable

# -------------------------
# Definiciones básicas
# -------------------------

# Palabras clave del lenguaje
PALABRAS_CLAVE = {
    # contenedores / estructura
    "ejercito", "global", "var", "mision", "severidad", "estricto", "advertencia",
    "revisar", "ejecutar", "confirmar",
    # control de flujo
    "si", "por", "defecto", "estrategia", "atacar", "mientras",
    "retirada", "con", "abortar", "avanzar",
    # literales lógicos y nulo
    "afirmativo", "negativo", "nulo",
    # misiones de ambiente
    "reportar", "recibir", "clasificarNumero", "clasificarMensaje", "azar",
    "aRangoSuperior", "aRangoInferior", "acampar", "calibre", "truncar",
}

# Operadores multi-caracter que deben probarse antes que los de 1 caracter
MULTI_OPS = [
    r"\|\|", r"&&", r"==", r"!=", r"<=", r">=", r"\+=",
    r"-=", r"\*=", r"/=", r"%="
]

# Operadores de 1 caracter
SINGLE_OPS = [
    r"=", r"\+", r"-", r"\*", r"/", r"%", r"<", r">", r"!"
]

# Símbolos de puntuación / separación
PUNCT = [
    r"\(", r"\)", r"\{", r"\}", r"\[", r"\]", r"\.", r",", r":"
]

# Se formulan Regex no capturantes para un análisis posterior
OPS_RE = "(?:" + "|".join(MULTI_OPS + SINGLE_OPS) + ")"
PUNCT_RE = "(?:" + "|".join(PUNCT) + ")"

# Regex de tokens primarios
# Orden es importante: primero comentarios y espacios, luego NL, luego tokens más largos, etc.
TOKEN_SPEC = [
    # Comentarios
    ("COMENT_BLOQ", r"/\*(?:[^*]|\*[^/])*\*/"),
    ("COMENT_LINEA", r"//[^\n]*(?:\r?\n)?"),

    # Espacios (excepto saltos de línea)
    ("ESPACIO", r"[ \t\f\v\r]+"),

    # Saltos de línea (NL) — opcionalmente se pueden emitir
    ("NL", r"(?:\r?\n)+"),

    # Cadenas (doble comilla, sin saltos de línea)
    ("CADENA", r"\"[^\"\n]*\""),

    # Números (flotantes primero, luego enteros)
    ("NUM_FLOTANTE", r"[0-9]+\.[0-9]+"),
    ("NUM_ENTERO", r"[0-9]+"),

    # Operadores
    ("OPERADOR",     OPS_RE),   

    # Símbolos
    ("SIMBOLO",      PUNCT_RE),

    # Identificadores
    ("IDENT", r"[A-Za-z_][A-Za-z0-9_]*"),
]

MASTER_REGEX = "|".join(f"(?P<{nombre}>{patron})" for (nombre, patron) in TOKEN_SPEC)
MASTER_RE = re.compile(MASTER_REGEX)

# -------------------------
# Estructuras de datos
# -------------------------

@dataclass
class Token:
    lexema: str
    tipo: str
    atributos: Dict[str, Any]

class ExploradorError(Exception):
    pass

# -------------------------
# Explorador
# -------------------------

class Explorador:
    def __init__(self, con_nuevaslineas: bool = False, tolerante: bool = False) -> None:
        self.con_nuevaslineas = con_nuevaslineas
        self.tolerante = tolerante

    def tokenizar(self, texto: str) -> List[Token]:
        tokens: List[Token] = []
        linea = 1
        linea_inicio = 0
        pos = 0
        longitud = len(texto)

        for m in MASTER_RE.finditer(texto):
            inicio, fin = m.start(), m.end()
            if inicio != pos:
                # Hay caracteres no reconocidos entre el último match y este
                bad_chunk = texto[pos:inicio]
                # Si sólo son espacios no contemplados, actualizamos línea/columna correctamente
                # pero en general tratamos esto como error.
                if not self._consume_desconocido(bad_chunk, linea, pos - linea_inicio, texto, tokens):
                    col = pos - linea_inicio + 1
                    excerpt = bad_chunk[:20].replace("\n", "\\n")
                    msg = f"Carácter no reconocido en fila {linea}, columna {col}: '{excerpt}'"
                    if self.tolerante:
                        tokens.append(Token(bad_chunk, "ERROR", linea, col, {"motivo": "desconocido"}))
                    else:
                        raise ExploradorError(msg)

                # Ajuste de línea/col ya realizado por _consume_desconocido
                # recomputar linea_inicio si terminó en NL
                # Nota: _consume_desconocido no cambia linea_inicio, así que no usar esto aquí.

            tipo = m.lastgroup
            lexema = m.group(tipo)

            # Posición del token
            tok_linea = linea
            tok_col = m.start() - linea_inicio + 1

            # Actualiza contadores si es NL
            if tipo == "NL":
                if self.con_nuevaslineas:
                    attrs = {"fila": tok_linea, "columna": tok_col}
                    tokens.append(Token(lexema, "NL", attrs))
                # contar saltos
                nl_count = lexema.count("\n")
                linea += nl_count
                # último \n redefine inicio de línea
                last_nl = lexema.rfind("\n")
                if last_nl != -1:
                    linea_inicio = m.start() + last_nl + 1

            elif tipo in ("ESPACIO", "COMENT_LINEA", "COMENT_BLOQ"):
                # Ignorar
                pass

            else:
                # Clasificar y construir atributos
                tipo, attrs = self._clasificar(tipo, lexema)
                attrs.update({"fila": tok_linea, "columna": tok_col})
                tokens.append(Token(lexema, tipo, attrs))

            pos = fin

        # Sobra texto sin reconocer al final
        if pos < longitud:
            bad_chunk = texto[pos:longitud]
            if not self._consume_desconocido(bad_chunk, linea, pos - linea_inicio, texto, tokens):
                col = pos - linea_inicio + 1
                excerpt = bad_chunk[:20].replace("\n", "\\n")
                msg = f"Carácter no reconocido al final en fila {linea}, columna {col}: '{excerpt}'"
                if self.tolerante:
                    attrs = {"fila": linea, "columna": col, "motivo": "desconocido"}
                    tokens.append(Token(bad_chunk, "ERROR", attrs))
                else:
                    raise ExploradorError(msg)

        return tokens

    def _clasificar(self, tipo: str, lexema: str) -> Tuple[str, Dict[str, Any]]:
        """Devuelve (tipo, atributos) normalizados para la tabla Lexema/Tipo/Atributos."""
        if tipo == "IDENT":
            if lexema in PALABRAS_CLAVE:
                return ("PALABRA_CLAVE", {})
            return ("IDENT", {})

        if tipo == "NUM_ENTERO":
            return ("NUM_ENTERO", {})

        if tipo == "NUM_FLOTANTE":
            return ("NUM_FLOTANTE", {})

        if tipo == "CADENA":
            return ("CADENA", {"valor": lexema[1:-1]})  # sin comillas

        if tipo == "OPERADOR":
            return ("OPERADOR", {})

        if tipo == "SIMBOLO":
            return ("SIMBOLO", {})

        # Fallback (No se sabe con exactitud)
        return (tipo, {})

    def _consume_desconocido(self, chunk: str, linea: int, col0: int, texto: str, tokens: List[Token]) -> bool:
        """
        Intenta consumir secuencias desconocidas formadas por espacios o controla NL manualmente.
        Devuelve True si pudo manejarlo sin error, False si debe levantarse ExploradorError.
        """
        if not chunk:
            return True

        # Si contiene caracteres imprimibles no-espacio distintos a \n, se trata como error
        if re.search(r"[^\s]", chunk.replace("\n", "")):
            return False

        return True

# -------------------------
# Utilidades de salida
# -------------------------

# Genera un texto con los tokens, cada uno en formato:
# <"Tipo de componente léxico", "Texto del componente léxico", “Atributos adicionales del componente”>
def tokens_a_texto(tokens: Iterable[Token]) -> str:
    lineas = []
    for t in tokens:
        attrs = json.dumps(t.atributos, ensure_ascii=False)
        lineas.append(f'<{t.tipo}, {t.lexema}, {attrs}>')
    return "\n".join(lineas)


def tokens_a_tabla(tokens: Iterable[Token]) -> str:
    # Tabla simple alineada
    filas = [("Lexema", "Tipo", "Atributos")]
    for t in tokens:
        attrs = json.dumps(t.atributos, ensure_ascii=False)
        filas.append((t.lexema, t.tipo, attrs))

    # Ancho de columnas
    anchos = [max(len(fila[i]) for fila in filas) for i in range(len(filas[0]))]
    lineas = []
    for i, fila in enumerate(filas):
        linea = " | ".join(val.ljust(anchos[j]) for j, val in enumerate(fila))
        lineas.append(linea)
        if i == 0:
            lineas.append("-+-".join("-" * w for w in anchos))
    return "\n".join(lineas)

# -------------------------
# CLI
# -------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Explorador (Explorador) para C-rvicio Militar: Texto -> Regex -> Lista"
    )
    parser.add_argument("fuente", nargs="?", default="-",
                        help="Archivo fuente a leer, o '-' para stdin (default: '-')")
    parser.add_argument("--json", action="store_true",
                        help="Imprimir salida como JSON")
    parser.add_argument("--tabla", action="store_true",
                        help="Imprimir salida como tabla (ignorado si --json está presente)")
    parser.add_argument("--include-nl", action="store_true",
                        help="Incluir tokens NL (saltos de línea)")
    parser.add_argument("--tolerant", action="store_true",
                        help="En lugar de fallar, genera tokens ERROR para caracteres desconocidos")

    args = parser.parse_args()

    # Leer texto
    if args.fuente == "-" or args.fuente is None:
        source = sys.stdin.read()
    else:
        with open(args.fuente, "r", encoding="utf-8") as f:
            source = f.read()

    exp = Explorador(con_nuevaslineas=args.include_nl, tolerante=args.tolerant)
    try:
        tokens = exp.tokenizar(source)
    except ExploradorError as e:
        print(f"Error léxico: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        out = [asdict(t) for t in tokens]
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.tabla:
        print(tokens_a_tabla(tokens))
    else:
        print(tokens_a_texto(tokens))


if __name__ == "__main__":
    main()
