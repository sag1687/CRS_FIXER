def classFactory(iface):
    from .quick_crs_fixer import QuickCRSFixer

    return QuickCRSFixer(iface)
