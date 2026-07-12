"""Qt5/Qt6 compatibility helpers for QGIS PyQt."""


def _alias(container, legacy_name, enum_group, enum_name):
    if hasattr(container, legacy_name) or not hasattr(container, enum_group):
        return
    group = getattr(container, enum_group)
    if hasattr(group, enum_name):
        setattr(container, legacy_name, getattr(group, enum_name))


def ensure_qt_compat(qt):
    aliases = (
        ("AlignCenter", "AlignmentFlag", "AlignCenter"),
        ("KeepAspectRatio", "AspectRatioMode", "KeepAspectRatio"),
        ("LeftDockWidgetArea", "DockWidgetArea", "LeftDockWidgetArea"),
        ("RightDockWidgetArea", "DockWidgetArea", "RightDockWidgetArea"),
        ("SmoothTransformation", "TransformationMode", "SmoothTransformation"),
        ("UserRole", "ItemDataRole", "UserRole"),
    )
    for legacy_name, enum_group, enum_name in aliases:
        _alias(qt, legacy_name, enum_group, enum_name)
    return qt


def ensure_qframe_compat(qframe):
    if hasattr(qframe, "Shape"):
        for name in ("HLine", "VLine", "NoFrame"):
            if not hasattr(qframe, name) and hasattr(qframe.Shape, name):
                setattr(qframe, name, getattr(qframe.Shape, name))
    return qframe
