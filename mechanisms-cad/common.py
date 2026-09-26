"""Utilidades compartidas para generar mecanismos planos (eslabones tipo barra
con orejas redondeadas y pines de articulacion) usando CadQuery / OCC.

Todas las longitudes en milimetros. Estas son piezas de validacion cinematica:
el ancho, espesor y diametro de pasador NO provienen del informe (que solo da
las longitudes cinematicas L1..L4), son valores de diseno razonables elegidos
para poder generar solidos 3D representativos.
"""
import math
import cadquery as cq


def _angle_deg(p1, p2):
    return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))


def _dist(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def bar_link(p1, p2, width, thickness, hole_d, extra_holes=None):
    """Eslabon tipo barra (capsula) entre dos puntos p1->p2 (XY, mm), con
    agujeros pasantes en cada extremo (articulaciones) y opcionalmente
    agujeros adicionales en puntos intermedios dados en coordenadas locales
    (fraccion 0..1 a lo largo de p1->p2)."""
    D = _dist(p1, p2)
    ang = _angle_deg(p1, p2)
    mid = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)

    profile = cq.Workplane("XY").slot2D(D + width, width, angle=0)
    solid = profile.extrude(thickness)
    solid = solid.faces(">Z").workplane().pushPoints([(-D / 2, 0), (D / 2, 0)]).hole(hole_d)

    if extra_holes:
        pts = [(-D / 2 + f * D, 0) for f in extra_holes]
        solid = solid.faces(">Z").workplane().pushPoints(pts).hole(hole_d)

    solid = solid.rotate((0, 0, 0), (0, 0, 1), ang).translate((mid[0], mid[1], 0))
    return solid


def pin(center_xy, diameter, z0, z1):
    x, y = center_xy
    h = z1 - z0
    return (
        cq.Workplane("XY", origin=(x, y, z0))
        .circle(diameter / 2.0)
        .extrude(h)
    )


def guide_slot_link(pivot_xy, angle_deg, u_body_start, u_body_end,
                     u_slot_start, u_slot_end, body_width, slot_width,
                     thickness, pivot_hole_d):
    """Eslabon-guia con ranura pasante (para el mecanismo biela-manivela
    invertido). 'u' es la coordenada local a lo largo del eje del eslabon,
    medida desde el pivote (pivot_xy). El pivote esta en u=0."""
    body_len = u_body_end - u_body_start
    body_mid_u = (u_body_start + u_body_end) / 2.0

    body = (
        cq.Workplane("XY")
        .slot2D(body_len + body_width, body_width, angle=0)
        .extrude(thickness)
        .translate((body_mid_u, 0, 0))
    )

    slot_len = u_slot_end - u_slot_start
    slot_mid_u = (u_slot_start + u_slot_end) / 2.0
    cutter = (
        cq.Workplane("XY")
        .slot2D(slot_len + slot_width, slot_width, angle=0)
        .extrude(thickness)
        .translate((slot_mid_u, 0, 0))
    )
    body = body.cut(cutter)

    body = body.faces(">Z").workplane().pushPoints([(0, 0)]).hole(pivot_hole_d)

    body = body.rotate((0, 0, 0), (0, 0, 1), angle_deg).translate((pivot_xy[0], pivot_xy[1], 0))
    return body


def slider_block(pivot_xy, angle_deg, u_center, block_len, block_width,
                  thickness, hole_d):
    """Bloque deslizante que corre dentro de la ranura de guide_slot_link,
    centrado en u_center (coordenada local sobre el eje del eslabon-guia) y
    con un agujero para el pasador que lo une a la manivela."""
    blk = (
        cq.Workplane("XY")
        .rect(block_len, block_width)
        .extrude(thickness)
        .translate((u_center, 0, 0))
    )
    blk = blk.faces(">Z").workplane().pushPoints([(u_center, 0)]).hole(hole_d)
    blk = blk.rotate((0, 0, 0), (0, 0, 1), angle_deg).translate((pivot_xy[0], pivot_xy[1], 0))
    return blk
