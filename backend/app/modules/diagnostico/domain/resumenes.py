"""Del dato al mensaje para el productor (informe 08, sección 7): sin jerga y con un solo número."""


def numero(valor: float, decimales: int = 0) -> str:
    """Formato colombiano: 1.255 y 27,6."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def textura_usda(arena: float, limo: float, arcilla: float) -> str:
    """Clase textural del triángulo del USDA, en español. Los porcentajes se normalizan a 100."""
    total = arena + limo + arcilla
    if total <= 0:
        raise ValueError("Textura sin datos.")
    arena, limo, arcilla = (100 * x / total for x in (arena, limo, arcilla))

    if limo + 1.5 * arcilla < 15:
        return "Arenoso"
    if limo + 2 * arcilla < 30:
        return "Arenoso franco"
    if (7 <= arcilla < 20 and arena > 52) or (arcilla < 7 and limo < 50):
        return "Franco arenoso"
    if 7 <= arcilla < 27 and 28 <= limo < 50 and arena <= 52:
        return "Franco"
    if limo >= 80 and arcilla < 12:
        return "Limoso"
    if limo >= 50 and arcilla < 27:
        return "Franco limoso"
    if 20 <= arcilla < 35 and limo < 28 and arena > 45:
        return "Franco arcillo arenoso"
    if 27 <= arcilla < 40 and 20 < arena <= 45:
        return "Franco arcilloso"
    if 27 <= arcilla < 40 and arena <= 20:
        return "Franco arcillo limoso"
    if arcilla >= 35 and arena > 45:
        return "Arcillo arenoso"
    if arcilla >= 40 and limo >= 40:
        return "Arcillo limoso"
    return "Arcilloso"


def clase_ph(ph: float) -> str:
    if ph < 5.5:
        return "muy ácido"
    if ph < 6.5:
        return "ácido"
    if ph < 7.4:
        return "neutro"
    return "alcalino"


def clase_humedad(theta_m3_m3: float) -> str:
    """Rangos generales de humedad volumétrica en la zona de raíces (SMAP)."""
    if theta_m3_m3 < 0.15:
        return "seca"
    if theta_m3_m3 < 0.30:
        return "con humedad adecuada"
    return "muy húmeda"


def clase_ndvi(ndvi: float) -> str:
    if ndvi < 0.2:
        return "suelo desnudo o casi sin plantas"
    if ndvi < 0.4:
        return "vegetación escasa"
    if ndvi < 0.6:
        return "vegetación moderada"
    return "vegetación densa"


def resumen_clima(lluvia_anual_mm: float, t_media_c: float, anio_inicio: int, anio_fin: int) -> str:
    return (
        f"{numero(lluvia_anual_mm)} mm de lluvia al año y {numero(t_media_c, 1)} °C en promedio "
        f"({anio_inicio}–{anio_fin})"
    )


def resumen_humedad(theta_m3_m3: float, dias: int) -> str:
    return (
        f"Tierra {clase_humedad(theta_m3_m3)}: {numero(theta_m3_m3 * 100)} % de humedad "
        f"en la zona de raíces (últimos {dias} días)"
    )


def resumen_suelo(arena: float, limo: float, arcilla: float, ph: float | None, materia_organica: float | None) -> str:
    partes = [textura_usda(arena, limo, arcilla)]
    if ph is not None:
        partes.append(f"pH {numero(ph, 1)} ({clase_ph(ph)})")
    if materia_organica is not None:
        partes.append(f"{numero(materia_organica, 1)} % de materia orgánica")
    if len(partes) == 3:
        return f"{partes[0]}, {partes[1]} y {partes[2]}"
    return ", ".join(partes)


def resumen_verdor(ndvi: float) -> str:
    return f"NDVI {numero(ndvi, 2)}: {clase_ndvi(ndvi)}"
