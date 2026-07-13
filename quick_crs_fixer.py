import os

from qgis.core import Qgis, QgsProject
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog

from .qt_compat import ensure_qt_compat

from .i18n import normalize_language, text
from .logic.detector import CRSDetector
from .logic.fixer import OneClickFixer
from .logic.suggest import SmartSuggest
from .ui.dock_widget import QuickCRSDockWidget

ensure_qt_compat(Qt)


class QuickCRSFixer:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.language = "it"

        # Inizializzazione moduli logici
        self.detector = CRSDetector(self.iface)
        self.suggest = SmartSuggest(self.iface)
        self.fixer = OneClickFixer(self.iface)

        self.action = None
        self.dockwidget = None

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "ICONA.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(self.plugin_dir, "icon.png")

        self.action = QAction(
            QIcon(icon_path), "Quick CRS Fixer", self.iface.mainWindow()
        )
        self.action.triggered.connect(self.run)
        self.iface.addVectorToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu("&Quick CRS Fixer", self.action)

        # Inizializzazione DockWidget
        self.dockwidget = QuickCRSDockWidget(self.iface.mainWindow())
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
        self.dockwidget.hide()

        # Connessione segnali UI
        self.dockwidget.refreshRequested.connect(self.scan_layers)
        self.dockwidget.fixRequested.connect(self.apply_fix)
        self.dockwidget.deepScanRequested.connect(self.run_deep_scan)
        self.dockwidget.languageChanged.connect(self.set_language)

        # Connessione segnali QGIS
        QgsProject.instance().layersAdded.connect(self.on_layers_added)

    def tr(self, key, **kwargs):
        return text(key, self.language, **kwargs)

    def set_language(self, language):
        self.language = normalize_language(language)
        self.detector.set_language(self.language)
        self.suggest.set_language(self.language)
        self.fixer.set_language(self.language)
        if self.dockwidget and self.dockwidget.language != self.language:
            self.dockwidget.set_language(self.language)
        if self.dockwidget and self.dockwidget.isVisible():
            self.scan_layers()

    def unload(self):
        if self.action:
            self.iface.removePluginVectorMenu("&Quick CRS Fixer", self.action)
            self.iface.removeVectorToolBarIcon(self.action)

        if self.dockwidget:
            self.iface.mainWindow().removeDockWidget(self.dockwidget)

        try:
            QgsProject.instance().layersAdded.disconnect(self.on_layers_added)
        except (RuntimeError, TypeError):
            pass

    def on_layers_added(self, layers):
        has_new_issues = False
        for layer in layers:
            data = self.detector.check_layer(layer)
            if data:
                has_new_issues = True
                self.iface.messageBar().pushMessage(
                    "Quick CRS Fixer",
                    self.tr("message.layer_problem", layer=layer.name()),
                    level=Qgis.Warning,
                    duration=3,
                )

        if has_new_issues and self.dockwidget and self.dockwidget.isVisible():
            self.scan_layers()

    def scan_layers(self):
        layers = QgsProject.instance().mapLayers().values()
        all_issues = {}
        for layer in layers:
            data = self.detector.check_layer(layer)
            if data:
                data["name"] = layer.name()
                data["suggestion"] = self.suggest.suggest_crs(layer)
                all_issues[layer.id()] = data

        if self.dockwidget:
            self.dockwidget.update_list(all_issues)
            self.dockwidget.update_resolved_list(
                self.dockwidget.resolved_issues
            )

    def run_deep_scan(self, layer_id, manual_query=""):
        try:
            layer = QgsProject.instance().mapLayer(layer_id)
            if not layer:
                return

            result = self.suggest.deep_scan(layer, manual_query)
            if result:
                if layer_id in self.dockwidget.current_issues:
                    self.dockwidget.current_issues[layer_id][
                        "suggestion"
                    ] = result
                    self.dockwidget.on_selection_changed()
                    self.iface.messageBar().pushMessage(
                        "Deep Scan OSM",
                        self.tr("deep_scan.success", name=result["name"]),
                        level=Qgis.Success,
                        duration=5,
                    )
                    for i in range(self.dockwidget.tree.topLevelItemCount()):
                        item = self.dockwidget.tree.topLevelItem(i)
                        if item.data(0, Qt.UserRole) == layer_id:
                            for j in range(item.childCount()):
                                item.child(j).setText(1, result["name"])
            else:
                self.iface.messageBar().pushMessage(
                    "Deep Scan OSM",
                    self.tr("deep_scan.no_result"),
                    level=Qgis.Warning,
                    duration=5,
                )
                self.dockwidget.on_selection_changed()
        except Exception as e:
            self.iface.messageBar().pushMessage(
                self.tr("dialog.error"),
                self.tr("deep_scan.error", error=e),
                level=Qgis.Critical,
                duration=5,
            )

    def apply_fix(self, layer_id, action_type, params):
        try:
            if action_type == "fix_all":
                layers = {}
                for l_id in QgsProject.instance().mapLayers():
                    data = self.detector.check_layer(
                        QgsProject.instance().mapLayer(l_id)
                    )
                    if data:
                        layers[l_id] = data

                count = self.fixer.fix_all(layers, self.suggest)
                self.iface.messageBar().pushMessage(
                    self.tr("action.success"),
                    self.tr("action.fixed_count", count=count),
                    level=Qgis.Success,
                )
                self.scan_layers()
                return

            layer = QgsProject.instance().mapLayer(layer_id)
            if not layer:
                return

            layer_name = layer.name()

            if action_type == "reproject_resolved":
                if layer_id in self.dockwidget.resolved_issues:
                    suggestion = self.dockwidget.resolved_issues[layer_id][
                        "suggestion"
                    ]
                else:
                    return
            else:
                if layer_id in self.dockwidget.current_issues:
                    suggestion = self.dockwidget.current_issues[layer_id][
                        "suggestion"
                    ]
                else:
                    suggestion = self.suggest.suggest_crs(layer)

            suggestion_id = suggestion["id"]
            if action_type == "reproject_resolved":
                if (
                    self.dockwidget.resolved_combo.isVisible()
                    and self.dockwidget.resolved_combo.currentData()
                ):
                    suggestion_id = (
                        self.dockwidget.resolved_combo.currentData()
                    )
            else:
                if (
                    self.dockwidget.epsg_combo.isVisible()
                    and self.dockwidget.epsg_combo.currentData()
                ):
                    suggestion_id = self.dockwidget.epsg_combo.currentData()

            success = False
            if action_type in ["assign", "reproject", "reproject_resolved"]:
                safe_sugg_id = suggestion_id.replace(":", "_")
                default_name = f"{layer_name}_{safe_sugg_id}.gpkg"
                home_dir = os.path.expanduser("~")

                file_path, _ = QFileDialog.getSaveFileName(
                    self.dockwidget,
                    self.tr("action.save_title"),
                    os.path.join(home_dir, "Scrivania", default_name),
                    "GeoPackage (*.gpkg)",
                )

                if not file_path:
                    self.iface.messageBar().pushMessage(
                        self.tr("action.cancelled.title"),
                        self.tr("action.cancelled"),
                        level=Qgis.Info,
                        duration=3,
                    )
                    return

                if action_type == "assign":
                    success = self.fixer.assign_crs(
                        layer, suggestion_id, file_path
                    )
                elif action_type in ["reproject", "reproject_resolved"]:
                    success = self.fixer.reproject_layer(
                        layer, suggestion_id, file_path
                    )

            if success:
                new_layer_id = success
                if action_type in ["assign", "reproject"]:
                    # Aggiunge al tab risolti per permettere la riproiezione
                    # finale
                    self.dockwidget.resolved_issues[new_layer_id] = {
                        "name": os.path.basename(file_path),
                        "suggestion": suggestion,
                    }
                elif action_type == "reproject_resolved":
                    # Aggiorna il layer ID
                    if layer_id in self.dockwidget.resolved_issues:
                        del self.dockwidget.resolved_issues[layer_id]
                    self.dockwidget.resolved_issues[new_layer_id] = {
                        "name": os.path.basename(file_path),
                        "suggestion": suggestion,
                    }

                self.iface.messageBar().pushMessage(
                    self.tr("action.success"),
                    self.tr(
                        "action.fix_applied",
                        layer=layer_name,
                        file_name=os.path.basename(file_path),
                    ),
                    level=Qgis.Success,
                )
                self.scan_layers()
        except Exception as e:
            self.iface.messageBar().pushMessage(
                self.tr("dialog.error"),
                self.tr("action.fix_error", error=e),
                level=Qgis.Critical,
                duration=5,
            )

    def run(self):
        if self.dockwidget:
            if self.dockwidget.isVisible():
                self.dockwidget.hide()
            else:
                self.dockwidget.show()
                self.scan_layers()
