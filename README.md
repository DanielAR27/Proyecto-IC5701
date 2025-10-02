# Explorador Léxico – Lenguaje **C-rvicio Militar**

## Integrantes
- Daniel Alemán Ruiz  
- José Julián Brenes Garro  
- Luis Ángel Meza Chavarría  
- Oscar Roni Ordoñez  
- Sebastián Calvo Hernández  

## Profesor
- Aurelio Sanabria Rodríguez  
- Curso: IC-5701 – Compiladores e Intérpretes  
- Instituto Tecnológico de Costa Rica (ITCR)

---

## Introducción
Este repositorio contiene el **explorador léxico** (lexer) del lenguaje **C-rvicio Militar**.  
El explorador es la primera etapa del proceso de compilación: **lee texto fuente y produce una lista de tokens** con su **lexema**, **tipo** y **atributos**.  
Flujo general: Texto fuente → Expresiones regulares → Lista de tokens


---

## ¿Cómo funciona?
El archivo principal es `explorador.py`. Internamente:

1. **Tabla de patrones (regex)**: define reglas para comentarios, espacios, saltos de línea, cadenas, números, operadores, símbolos e identificadores.
2. **Clasificación**:
   - Si un identificador coincide con una **palabra clave** del lenguaje, se reclasifica como `PALABRA_CLAVE`.
   - Números enteros y flotantes guardan su valor en atributos.
   - Cadenas guardan su contenido sin comillas.
3. **Ignora** espacios y comentarios.
4. **Opcional**: puede emitir tokens de salto de línea (`NL`) y operar en **modo tolerante** para no detenerse ante caracteres desconocidos.
5. **Salida**:
   - Por defecto imprime una **tabla** (`Lexema | Tipo | Atributos | Fila | Col`).
   - Con `--json` imprime **JSON** (útil para integrarlo con un parser/analizador posterior).

### Tokens reconocidos (resumen)
- **Palabras clave**: `ejercito`, `global`, `var`, `mision`, `severidad`, `estricto`, `advertencia`,  
  `revisar`, `ejecutar`, `confirmar`, `si`, `por`, `defecto`, `estrategia`, `atacar`, `mientras`,  
  `retirada`, `con`, `abortar`, `avanzar`, `afirmativo`, `negativo`, `nulo`,  
  `reportar`, `recibir`, `clasificarNumero`, `clasificarMensaje`, `azar`,  
  `aRangoSuperior`, `aRangoInferior`, `acampar`, `calibre`, `truncar`.
- **Números**: `NUM_ENTERO`, `NUM_FLOTANTE`.
- **Cadenas**: `CADENA` (entre comillas dobles, sin saltos de línea).
- **Operadores**: `|| && == != <= >= += -= *= /= %= = + - * / % < > !`
- **Símbolos**: `(` `)` `{` `}` `[` `]` `.` `,` `:`
- **Identificadores**: `IDENT` (letra o `_` seguido de letras, dígitos o `_`).

---

## Requisitos
- Python **3.10** o superior.

---

## Uso básico

### 1) Ejecutar leyendo desde un archivo
```bash
# Linux
python3 explorador.py ruta/al/archivo.crv
```

### 2) Leer desde stdin

```bash
cat archivo.crv | python3 explorador.py
```

### 3) Opciones de línea de comandos

- `--json`
Imprime la lista de tokens en JSON.

-- `--tabla`
Imprime la lista como una tabla.

- `--include-nl`
Incluye tokens NL (saltos de línea).

- `--tolerant`
No se detiene ante caracteres ilegales; genera tokens `ERROR`.

Ejemplos:

```bash
python3 explorador.py ejemplo.crv --json
python3 explorador.py ejemplo.crv --tabla
python3 explorador.py ejemplo.crv --include-nl
python3 explorador.py ejemplo.crv --tolerant --json > tokens.json
```

---

## Ejemplo rápido (válido)
`ejemplo.crv`

```txt
ejercito Finanzas {
  global var x = 10
  x += 5
  reportar("ok")
}
```

**Comando**

```bash
python3 explorador.py ejemplo.crv --tabla
```

**Salida (tabla)**

```csharp
Lexema   | Tipo          | Atributos                                
---------+---------------+------------------------------------------
ejercito | PALABRA_CLAVE | {"fila": 1, "columna": 1}                
Finanzas | IDENT         | {"fila": 1, "columna": 10}               
{        | SIMBOLO       | {"fila": 1, "columna": 19}               
global   | PALABRA_CLAVE | {"fila": 2, "columna": 3}                
var      | PALABRA_CLAVE | {"fila": 2, "columna": 10}               
x        | IDENT         | {"fila": 2, "columna": 14}               
=        | OPERADOR      | {"fila": 2, "columna": 16}               
10       | NUM_ENTERO    | {"fila": 2, "columna": 18}               
x        | IDENT         | {"fila": 3, "columna": 3}                
+=       | OPERADOR      | {"fila": 3, "columna": 5}                
5        | NUM_ENTERO    | {"fila": 3, "columna": 8}                
reportar | PALABRA_CLAVE | {"fila": 4, "columna": 3}                
(        | SIMBOLO       | {"fila": 4, "columna": 11}               
"ok"     | CADENA        | {"valor": "ok", "fila": 4, "columna": 12}
)        | SIMBOLO       | {"fila": 4, "columna": 16}               
}        | SIMBOLO       | {"fila": 5, "columna": 1}  
```

---

## Ejemplo con error léxico
`error.crv`

```txt
ejercito Prueba {
    x = 10 @ 5
}
```

**1. Ejecución normal (estricto)**

```bash
python3 explorador.py error.crv
```

**Salida**

```bash
Error léxico: Carácter no reconocido en fila 2, columna 12: '@'
```

**2. Ejecución tolerante**

```bash
python3 explorador.py error.crv --tolerant
```

**Salida (tabla)**

```csharp
Lexema | Tipo   | Atributos                      
-------+--------+----------------------------------------------------
@      | ERROR  | {"fila": 2, "columna": 12, "motivo": "desconocido"}
```

---

### Salidas y formatos

- **Tabla** (por defecto): legible en consola para revisión rápida.

- **JSON** (`--json`): ideal para integrarlo con el analizador o pruebas automatizadas.

Ejemplo de redirección:

```bash
# Ejecutar el explorador y guardar en un archivo JSON
python3 explorador.py ejemplo.crv --json > tokens.json
```

---

## Notas

- El código fuente del explorador utiliza nombres en español sin tildes (por ejemplo, `tokenizar`, `Explorador`, `con_nuevaslineas`), de acuerdo con la preferencia del curso.

- Comentarios soportados: `// ...` y `/* ... */`.

- Si se requiere contar líneas explícitamente en la fase sintáctica, puede usarse          `--include-nl` para emitir NL.