# Mecanismos CAD (cuatro barras y biela-manivela invertido)

Modelos 3D parametricos generados con [CadQuery](https://cadquery.readthedocs.io/)
(kernel OpenCascade, el mismo tipo de nucleo geometrico que usa SolidWorks para
leer/escribir STEP) a partir de las longitudes de eslabon reportadas en la
seccion "4. Resultados y validacion en SolidWorks" del informe.

No se ejecuto SolidWorks (no esta disponible en este entorno en la nube, sin
GUI). En su lugar se reconstruyo la geometria real de cada mecanismo con un
kernel CAD equivalente y se exporto en formatos universales (STEP, STL) que
se pueden abrir directamente en SolidWorks, FreeCAD, Fusion 360, etc.

## Topologia reconstruida

Los angulos theta2/theta3 (cuatro barras) y Lcb/theta2 (biela-manivela
invertido) de la tabla del informe no alcanzan por si solos para saber que
convencion de numeracion de eslabones y que posicion de los pivotes fijos se
uso. Se reconstruyo la topologia resolviendo el lazo vectorial de posicion
para las dos mecanismos y comprobando que reproduce EXACTAMENTE los valores
tabulados en las 5 posiciones (theta1 = 0, 45, 90, 135, 180 grados). Ver
`validate_kinematics.py`.

### Mecanismo de cuatro barras

- Pivote fijo A = (0,0), pivote fijo D = (35,0)  (Delta X=35, Delta Y=0 => L4)
- L1 = 5 mm: manivela A->B (entrada, angulo theta1)
- L2 = 30 mm: acoplador B->C (angulo theta2)
- L3 = 60 mm: balancin D->C (angulo theta3)
- L4 = 35 mm: bancada A->D (fija)
- Lazo vectorial: `A + L1<theta1 + L2<theta2 = D + L3<theta3`, resuelto por
  interseccion de circunferencias (rama "abierta").

### Mecanismo de biela-manivela invertido

- Pivote fijo A = (0,0), pivote fijo C = (50,0)
- L1 = 80 mm: manivela A->B (angulo theta1)
- L3 = 50 mm: bancada A->C (fija)
- Lcb = |B - C|: posicion del bloque deslizante dentro de la ranura del
  eslabon guiado, medida desde C
- theta2: angulo del eslabon-guia (direccion C->B)
- Rango fisico de Lcb en una vuelta completa: 30 mm (theta1=0) a 130 mm
  (theta1=180). La ranura del eslabon-guia se dimensiono para cubrir ese
  rango completo, no solo la posicion exportada.

## Resultado de la validacion (Python vs. tabla del informe)

| Mecanismo | theta1 | Valor informe | Valor recalculado |
|---|---|---|---|
| Cuatro barras | 0..180 (5 puntos) | theta2, theta3 | coincide en las 5 posiciones |
| Biela-manivela invertido | 0..180 (5 puntos) | Lcb, theta2 | coincide en las 5 posiciones |

Ejecutar `python3 validate_kinematics.py` para ver el detalle numerico.

## Supuestos de diseno (no estan en el informe)

El informe solo da longitudes cinematicas (L1..L4, Lcb). Para generar
solidos 3D reales hacen falta ademas ancho, espesor y diametro de pasador de
cada eslabon; se eligieron valores de diseno razonables:

- Cuatro barras: ancho de barra 4 mm, espesor 3 mm, pasador 2 mm (acorde a la
  escala pequena del mecanismo, 5-60 mm).
- Biela-manivela invertido: ancho 9-10 mm, espesor 6 mm, pasador 5 mm (acorde
  a su escala mayor, 50-130 mm).

Todos los eslabones de un mismo mecanismo se modelaron en un unico plano/capa
(mismo rango de Z): es un modelo de validacion cinematica planar, no un
ensamble listo para fabricar (en un diseno real cada eslabon iria en una capa
Z distinta para evitar interferencias entre barras que se cruzan).

## Archivos generados

`out/` contiene, para cada mecanismo, un ensamble 3D real (multi-cuerpo, con
un color distinto por eslabon y pasadores cilindricos en cada articulacion)
en la posicion theta1 = 45 grados:

- `fourbar_theta1_45.step` / `.stl`
- `invslidercrank_theta1_45.step` / `.stl`
- Capturas de referencia: `*_top.png` (vista en planta) y `*_iso.png` (vista
  isometrica)

## Regenerar en otra posicion

```bash
pip install cadquery
cd mechanisms-cad
python3 fourbar.py <theta1_en_grados> out/fourbar_theta1_XX
python3 invslidercrank.py <theta1_en_grados> out/invslidercrank_theta1_XX
```

Cada script imprime tambien B, C (o Lcb) y theta2/theta3 calculados para esa
posicion, para poder comparar contra SolidWorks o contra la tabla del
informe.
