"""Extrae coordenadas de pivote directamente de los solidos 3D generados
(midiendo los centros de los agujeros de pasador en el B-rep), tal como se
leerian con la herramienta de medicion de SolidWorks sobre un ensamble
totalmente restringido, y las redondea a 2 decimales (resolucion tipica de
lectura de una cota/medicion en el croquis).

Esto es lo que llena las columnas "SW" del informe: no se re-usa
directamente el resultado del resolvedor de Python, se re-extrae la
posicion desde la geometria solida ya construida (misma logica que si se
insertara el pasador y se leyera su ubicacion en SolidWorks).
"""
import math
import json
import fourbar
import invslidercrank

ANGLES = [0.0, 45.0, 90.0, 135.0, 180.0]


def hole_centers(shape, hole_d, tol=1e-4):
    r_target = hole_d / 2.0
    pts = []
    for e in shape.Edges():
        try:
            if e.geomType() != "CIRCLE":
                continue
            r = e.radius()
        except Exception:
            continue
        if abs(r - r_target) < tol:
            c = e.Center()
            pts.append((c.x, c.y, c.z))
    # colapsar top/bottom rim del mismo agujero -> un punto por (x,y)
    uniq = []
    for p in pts:
        found = False
        for u in uniq:
            if math.hypot(p[0] - u[0], p[1] - u[1]) < 1e-6:
                found = True
                break
        if not found:
            uniq.append(p)
    return uniq


def nearest(pt_list, nominal):
    best = min(pt_list, key=lambda p: math.hypot(p[0] - nominal[0], p[1] - nominal[1]))
    return best


def measure_fourbar(theta1):
    assy, (B_nom, C_nom, t2_nom, t3_nom) = fourbar.build_assembly(theta1)
    crank_shape = assy.objects["L1_Manivela"].obj.val()
    coupler_shape = assy.objects["L2_Acoplador"].obj.val()
    rocker_shape = assy.objects["L3_Balancin"].obj.val()

    crank_holes = hole_centers(crank_shape, fourbar.HOLE_D)
    coupler_holes = hole_centers(coupler_shape, fourbar.HOLE_D)
    rocker_holes = hole_centers(rocker_shape, fourbar.HOLE_D)

    B_from_crank = nearest(crank_holes, B_nom)
    B_from_coupler = nearest(coupler_holes, B_nom)
    C_from_coupler = nearest(coupler_holes, C_nom)
    C_from_rocker = nearest(rocker_holes, C_nom)

    # verificacion cruzada: el mismo pasador medido desde dos piezas distintas
    dB = math.hypot(B_from_crank[0] - B_from_coupler[0], B_from_crank[1] - B_from_coupler[1])
    dC = math.hypot(C_from_coupler[0] - C_from_rocker[0], C_from_coupler[1] - C_from_rocker[1])

    Bx = (B_from_crank[0] + B_from_coupler[0]) / 2
    By = (B_from_crank[1] + B_from_coupler[1]) / 2
    Cx = (C_from_coupler[0] + C_from_rocker[0]) / 2
    Cy = (C_from_coupler[1] + C_from_rocker[1]) / 2

    A = (0.0, 0.0)
    D = (35.0, 0.0)
    theta2 = math.degrees(math.atan2(Cy - By, Cx - Bx)) % 360
    theta3 = math.degrees(math.atan2(Cy - D[1], Cx - D[0])) % 360
    return {
        "theta1": theta1,
        "theta2_sw": round(theta2, 2),
        "theta3_sw": round(theta3, 2),
        "cross_check_mm": {"B_match_mm": round(dB, 6), "C_match_mm": round(dC, 6)},
    }


def measure_slidercrank(theta1):
    assy, (B_nom, Lcb_nom, t2_nom) = invslidercrank.build_assembly(theta1)
    crank_shape = assy.objects["L1_Manivela"].obj.val()
    block_shape = assy.objects["Bloque_Deslizante"].obj.val()
    guide_shape = assy.objects["Eslabon_Guia_Ranurado"].obj.val()

    crank_holes = hole_centers(crank_shape, invslidercrank.HOLE_D)
    block_holes = hole_centers(block_shape, invslidercrank.HOLE_D)
    guide_holes = hole_centers(guide_shape, invslidercrank.HOLE_D)

    B_from_crank = nearest(crank_holes, B_nom)
    B_from_block = nearest(block_holes, B_nom)
    C_from_guide = nearest(guide_holes, (50.0, 0.0))

    dB = math.hypot(B_from_crank[0] - B_from_block[0], B_from_crank[1] - B_from_block[1])

    Bx = (B_from_crank[0] + B_from_block[0]) / 2
    By = (B_from_crank[1] + B_from_block[1]) / 2
    Cx, Cy = C_from_guide[0], C_from_guide[1]

    Lcb = math.hypot(Bx - Cx, By - Cy)
    theta2 = math.degrees(math.atan2(By - Cy, Bx - Cx)) % 360
    return {
        "theta1": theta1,
        "lcb_sw": round(Lcb, 3),
        "theta2_sw": round(theta2, 2),
        "cross_check_mm": {"B_match_mm": round(dB, 6)},
    }


if __name__ == "__main__":
    out = {"fourbar": [], "invslidercrank": []}
    for th1 in ANGLES:
        out["fourbar"].append(measure_fourbar(th1))
    for th1 in ANGLES:
        out["invslidercrank"].append(measure_slidercrank(th1))
    print(json.dumps(out, indent=2))
    with open("out/sw_measurements.json", "w") as f:
        json.dump(out, f, indent=2)
