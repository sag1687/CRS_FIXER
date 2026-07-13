import os

from qgis.gui import QgsDockWidget
from qgis.PyQt.QtCore import Qt, QUrl, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from qgis.PyQt.QtGui import QIcon, QPixmap
from ..i18n import normalize_language, text
from ..qt_compat import ensure_qframe_compat, ensure_qt_compat
from .. import plugin_hub

ensure_qt_compat(Qt)
ensure_qframe_compat(QFrame)


class QuickCRSDockWidget(QgsDockWidget):
    fixRequested = pyqtSignal(str, str, str)
    refreshRequested = pyqtSignal()
    deepScanRequested = pyqtSignal(str, str)
    languageChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super(QuickCRSDockWidget, self).__init__(parent)
        self.setWindowTitle("Quick CRS Fixer")
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.current_issues = {}
        self.language = "it"
        self._issue_count = 0

        self.main_widget = QWidget()
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # UI Styling — shared SinoCloud family dark theme (see
        # plugin_hub.py), plus tree-specific tweaks for the dock.
        self.main_widget.setStyleSheet(plugin_hub.FAMILY_STYLE + """
            QTreeWidget {
                border: none;
                background-color: #1b2430;
                alternate-background-color: #22303e;
                color: #f2f5f8;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #2c4f70;
            }
        """)

        # Tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Tab 1: Fixer
        self.tab_fixer = QWidget()
        self.fixer_layout = QVBoxLayout(self.tab_fixer)
        self.fixer_layout.setContentsMargins(0, 0, 0, 0)
        self.fixer_layout.setSpacing(0)

        # Header
        self.header_frame = QFrame()
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(8, 8, 8, 8)
        self.stats_label = QLabel(self.tr("stats.problems", count=0))
        self.stats_label.setStyleSheet("font-size: 14px; color: #f59e0b;")
        self.header_layout.addWidget(self.stats_label)

        self.language_label = QLabel(self.tr("label.language"))
        self.language_combo = QComboBox()
        self.language_combo.addItem(plugin_hub.FLAG_IT + " Italiano", "it")
        self.language_combo.addItem(plugin_hub.FLAG_EN + " English", "en")

        self.refresh_btn = QPushButton(
            QIcon.fromTheme("view-refresh"), self.tr("button.refresh")
        )
        self.refresh_btn.clicked.connect(lambda: self.refreshRequested.emit())
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.language_label)
        self.header_layout.addWidget(self.language_combo)
        self.header_layout.addWidget(self.refresh_btn)
        self.fixer_layout.addWidget(self.header_frame)

        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            [self.tr("tree.fixer.col0"), self.tr("tree.fixer.col1")]
        )
        self.tree.setColumnWidth(0, 200)
        self.tree.setAlternatingRowColors(True)
        self.fixer_layout.addWidget(self.tree)
        # Details
        self.details_label = QLabel(self.tr("ui.empty_details"))
        self.details_label.setWordWrap(True)
        self.details_label.setStyleSheet(
            "padding: 8px; background-color: #1b2430; border-top: 1px solid "
            "#2c3a48;"
        )
        self.fixer_layout.addWidget(self.details_label)

        # Combo per vari EPSG
        self.epsg_combo = QComboBox()
        self.epsg_combo.hide()
        self.fixer_layout.addWidget(self.epsg_combo)

        # Actions
        self.actions_layout = QHBoxLayout()
        self.btn_assign = QPushButton(QIcon.fromTheme("symlink"), "Assign")
        self.btn_reproject = QPushButton(
            QIcon.fromTheme("transform-move"), "Reproject"
        )
        self.btn_deep_scan = QPushButton(
            QIcon.fromTheme("network-wireless"), "Deep Scan OSM"
        )
        self.btn_fix_all = QPushButton(
            QIcon.fromTheme("dialog-ok-apply"), "Fix All"
        )

        for btn in [
            self.btn_assign,
            self.btn_reproject,
            self.btn_deep_scan,
            self.btn_fix_all,
        ]:
            btn.setEnabled(False)
            self.actions_layout.addWidget(btn)

        self.fixer_layout.addLayout(self.actions_layout)

        # Tab 1.5: Resolved
        self.tab_resolved = QWidget()
        self.resolved_layout = QVBoxLayout(self.tab_resolved)
        self.resolved_layout.setContentsMargins(10, 10, 10, 10)
        self.resolved_layout.setSpacing(10)

        self.tree_resolved = QTreeWidget()
        self.tree_resolved.setHeaderLabels(
            [self.tr("tree.resolved.col0"), self.tr("tree.resolved.col1")]
        )
        self.tree_resolved.setColumnWidth(0, 200)
        self.tree_resolved.setAlternatingRowColors(True)
        self.resolved_layout.addWidget(self.tree_resolved)

        self.resolved_details = QLabel(self.tr("resolved.empty_details"))
        self.resolved_details.setWordWrap(True)
        self.resolved_details.setStyleSheet(
            "padding: 8px; background-color: #1b2430; border-top: 1px solid "
            "#2c3a48;"
        )
        self.resolved_layout.addWidget(self.resolved_details)

        self.resolved_combo = QComboBox()
        self.resolved_combo.hide()
        self.resolved_layout.addWidget(self.resolved_combo)

        self.btn_reproject_resolved = QPushButton(
            QIcon.fromTheme("transform-move"),
            self.tr("button.reproject_resolved"),
        )
        self.btn_reproject_resolved.setEnabled(False)
        self.resolved_layout.addWidget(self.btn_reproject_resolved)

        # Tab 2: Info
        self.tab_info = QWidget()
        self.info_layout = QVBoxLayout(self.tab_info)
        self.info_layout.setContentsMargins(10, 10, 10, 10)

        # Logo P
        self.logo_p_label = QLabel()
        logo_p_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "LOGO_P.png"
        )
        if os.path.exists(logo_p_path):
            pixmap_p = QPixmap(logo_p_path)
            self.logo_p_label.setPixmap(
                pixmap_p.scaled(
                    300,
                    300,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.logo_p_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_layout.addWidget(self.logo_p_label)

        # Logo Author
        self.logo_label = QLabel()
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "logo.jpg"
        )
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            self.logo_label.setPixmap(
                pixmap.scaled(
                    80,
                    80,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_layout.addWidget(self.logo_label)

        # Info Text
        self.info_label = QLabel(self._info_html())
        self.info_label.setOpenExternalLinks(True)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_layout.addWidget(self.info_label)

        # Inizio Licenze e Dati Esterni
        hline1 = QFrame()
        hline1.setFrameShape(QFrame.Shape.HLine)
        hline1.setStyleSheet(
            "background-color: #2c3a48; margin-top: 10px; margin-bottom: 5px;"
        )
        self.info_layout.addWidget(hline1)

        self.disclaimer_label = QLabel(self.tr("info.disclaimer"))
        self.disclaimer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_layout.addWidget(self.disclaimer_label)

        self.logos_layout = QHBoxLayout()

        # OSM
        self.osm_layout = QVBoxLayout()
        osm_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "osm"
        )
        osm_url = QUrl.fromLocalFile(osm_path).toString()
        self.osm_img = QLabel(
            f"<a href='https://www.openstreetmap.org/copyright'>"
            f"<img src='{osm_url}' width='50'></a>"
        )
        self.osm_img.setOpenExternalLinks(True)
        self.osm_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.osm_desc = QLabel(self.tr("info.osm"))
        self.osm_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.osm_layout.addWidget(self.osm_img)
        self.osm_layout.addWidget(self.osm_desc)

        # VLine
        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        vline.setStyleSheet("background-color: #2c3a48;")

        # Wikipedia
        self.wiki_layout = QVBoxLayout()
        wiki_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "Wikipedia-logo-v2.svg.png",
        )
        wiki_url = QUrl.fromLocalFile(wiki_path).toString()
        self.wiki_img = QLabel(
            f"<a href='https://it.wikipedia.org/'><img src='{wiki_url}' "
            f"width='50'></a>"
        )
        self.wiki_img.setOpenExternalLinks(True)
        self.wiki_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wiki_desc = QLabel(self.tr("info.wiki"))
        self.wiki_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wiki_layout.addWidget(self.wiki_img)
        self.wiki_layout.addWidget(self.wiki_desc)

        self.logos_layout.addLayout(self.osm_layout)
        self.logos_layout.addWidget(vline)
        self.logos_layout.addLayout(self.wiki_layout)
        self.info_layout.addLayout(self.logos_layout)

        hline2 = QFrame()
        hline2.setFrameShape(QFrame.Shape.HLine)
        hline2.setStyleSheet(
            "background-color: #2c3a48; margin-top: 5px; margin-bottom: 10px;"
        )
        self.info_layout.addWidget(hline2)
        # Fine Licenze e Dati Esterni

        # Altri Plugin — shared family drop-down (see plugin_hub.py)
        self.family_widget = plugin_hub.make_family_widget(
            "quick_crs_fixer", lang=self.language
        )
        self.info_layout.addWidget(self.family_widget)
        self.info_layout.addStretch()

        # Tab Help
        self.tab_help = QWidget()
        self.help_layout = QVBoxLayout(self.tab_help)
        self.help_layout.setContentsMargins(10, 10, 10, 10)
        self.help_browser = QTextBrowser()
        self.help_browser.setOpenExternalLinks(False)
        self.help_browser.setHtml(self._help_html())
        self.help_browser.setStyleSheet(
            "background-color: #1b2430; color: #c3ccd6; border: 1px solid "
            "#2c3a48; padding: 8px;"
        )
        self.help_layout.addWidget(self.help_browser)

        self.tabs.addTab(self.tab_fixer, self.tr("tab.fixer"))
        self.tabs.addTab(self.tab_resolved, self.tr("tab.resolved"))
        self.tabs.addTab(self.tab_help, self.tr("tab.help"))
        self.tabs.addTab(self.tab_info, self.tr("tab.info"))

        self.setWidget(self.main_widget)

        self.tree_resolved.itemSelectionChanged.connect(
            self.on_resolved_selection_changed
        )
        self.btn_reproject_resolved.clicked.connect(
            self.emit_reproject_resolved
        )
        self.resolved_issues = {}
        self.language_combo.currentIndexChanged.connect(
            self.on_language_changed
        )
        self.tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.btn_assign.clicked.connect(lambda: self.emit_fix("assign"))
        self.btn_reproject.clicked.connect(lambda: self.emit_fix("reproject"))
        self.btn_deep_scan.clicked.connect(self.emit_deep_scan)
        self.btn_fix_all.clicked.connect(
            lambda: self.fixRequested.emit("all", "fix_all", "")
        )
        self._retranslate_static()

    def tr(self, key, **kwargs):
        return text(key, self.language, **kwargs)

    def set_language(self, language):
        self.language = normalize_language(language)
        index = self.language_combo.findData(self.language)
        if index >= 0 and index != self.language_combo.currentIndex():
            was_blocked = self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(index)
            self.language_combo.blockSignals(was_blocked)
        self._retranslate_static()
        self.on_selection_changed()

    def on_language_changed(self, index):
        language = self.language_combo.itemData(index) or "it"
        self.set_language(language)
        self.languageChanged.emit(self.language)

    def _info_html(self):
        version_label = self.tr("info.version")
        return f"""
        <h2 style='color: #f2f5f8; text-align: center;'>Quick CRS Fixer</h2>
        <p style='text-align: center;'><b>{version_label} 2.0</b></p>
        <p style='text-align: center;'>Autore / Author:
          <b>Dott. Sarino Alfonso Grande</b></p>
        <p style='text-align: center;'>
          Website:
          <a href='https://sinocloud.it'
             style='color: #5b9bd5;'>sinocloud.it</a>
        </p>
        <p style='text-align: center;'>Email: sino.grande@gmail.com</p>
        """

    def _retranslate_static(self):
        self.stats_label.setText(
            self.tr("stats.problems", count=self._issue_count)
        )
        self.language_label.setText(self.tr("label.language"))
        self.refresh_btn.setText(self.tr("button.refresh"))
        self.refresh_btn.setToolTip(self.tr("button.refresh.tooltip"))
        self.btn_assign.setText(self.tr("button.assign"))
        self.btn_assign.setToolTip(self.tr("button.assign.tooltip"))
        self.btn_reproject.setText(self.tr("button.reproject"))
        self.btn_reproject.setToolTip(self.tr("button.reproject.tooltip"))
        self.btn_deep_scan.setText(self.tr("button.deep_scan"))
        self.btn_deep_scan.setToolTip(self.tr("button.deep_scan.tooltip"))
        self.btn_fix_all.setText(self.tr("button.fix_all"))
        self.btn_fix_all.setToolTip(self.tr("button.fix_all.tooltip"))
        self.btn_reproject_resolved.setText(
            self.tr("button.reproject_resolved")
        )
        self.btn_reproject_resolved.setToolTip(
            self.tr("button.reproject.tooltip")
        )
        self.tree.setHeaderLabels(
            [self.tr("tree.fixer.col0"), self.tr("tree.fixer.col1")]
        )
        self.tree_resolved.setHeaderLabels(
            [self.tr("tree.resolved.col0"), self.tr("tree.resolved.col1")]
        )
        self.tabs.setTabText(0, self.tr("tab.fixer"))
        self.tabs.setTabText(1, self.tr("tab.resolved"))
        self.tabs.setTabText(2, self.tr("tab.help"))
        self.tabs.setTabText(3, self.tr("tab.info"))
        self.help_browser.setHtml(self._help_html())
        self.info_label.setText(self._info_html())
        self.disclaimer_label.setText(self.tr("info.disclaimer"))
        self.osm_desc.setText(self.tr("info.osm"))
        self.wiki_desc.setText(self.tr("info.wiki"))
        self.family_widget.set_lang(self.language)
        if not self.tree.selectedItems():
            self.details_label.setText(self.tr("ui.empty_details"))
        if not self.tree_resolved.selectedItems():
            self.resolved_details.setText(self.tr("resolved.empty_details"))

    def _help_html(self):
        if self.language == "en":
            return """
        <h2>Quick CRS Fixer - Help</h2>
        <h3>Core workflow</h3>
        <ol>
          <li>Load one or more vector layers into the QGIS project.</li>
          <li>Open <b>Quick CRS Fixer</b> from the toolbar or the Vector
              menu.</li>
          <li>Use the <b>Language</b> selector to switch between Italian
              and English.</li>
          <li>Click <b>Refresh</b> to scan the loaded layers.</li>
          <li>Select a layer in <b>Detected Issues</b>.</li>
          <li>Read the EPSG suggestion and choose the most appropriate
              action at the bottom.</li>
        </ol>
        <h3>Assign and Reproject</h3>
        <ul>
          <li><b>Assign</b> writes the correct CRS on coordinates that are
              already expressed in that system. Use it when the coordinate
              numbers are right, but the CRS is missing or incorrectly
              declared.</li>
          <li><b>Reproject</b> creates a new layer in another CRS by
              transforming the coordinates. Use it after assigning the
              correct native CRS.</li>
          <li>The plugin saves the result as GeoPackage and replaces the
              original project layer with the fixed layer.</li>
        </ul>
        <h3>Deep Scan OSM</h3>
        <ol>
          <li>Select a problematic layer.</li>
          <li>Click <b>Deep Scan OSM</b>.</li>
          <li>The plugin searches useful text fields, queries Nominatim
              and Wikipedia, then compares the theoretical center with a
              list of candidate EPSG codes.</li>
          <li>If multiple plausible EPSG codes are found, choose the
              required one from the drop-down menu before applying the
              correction.</li>
        </ol>
        <h3>Fix All</h3>
        <p><b>Fix All</b> automatically assigns the suggested CRS to all
        flagged layers. Use it only when the suggestions are coherent;
        for critical data, check each layer manually.</p>
        <h3>Reassign EPSG</h3>
        <p>The <b>Reassign EPSG</b> tab lists recently fixed layers and
        allows an optional final reprojection to a selected EPSG.</p>
        <h3>Practical checks</h3>
        <ul>
          <li>Small coordinates such as 12, 42 often indicate
              EPSG:4326.</li>
          <li>Italian UTM coordinates often have X between 300000 and
              800000 and Y between 4000000 and 5300000.</li>
          <li>Gauss-Boaga uses false eastings around 1500000 or
              2520000.</li>
          <li>Deep Scan requires an internet connection and uses external
              services.</li>
        </ul>
        """
        return """
        <h2>Quick CRS Fixer - Help</h2>
        <h3>Workflow base</h3>
        <ol>
          <li>Carica uno o piu' layer vettoriali nel progetto QGIS.</li>
          <li>Apri <b>Quick CRS Fixer</b> dalla toolbar o dal menu
              Vettore.</li>
          <li>Usa il selettore <b>Lingua</b> per passare da italiano a
              inglese.</li>
          <li>Premi <b>Aggiorna</b> per analizzare i layer caricati.</li>
          <li>Seleziona un layer nella lista <b>Problemi Rilevati</b>.</li>
          <li>Leggi il suggerimento EPSG e scegli una delle azioni in
              basso.</li>
        </ol>
        <h3>Assign e Reproject</h3>
        <ul>
          <li><b>Assign</b> assegna il CRS corretto a coordinate gia' espresse
              in quel sistema. Usalo quando i numeri sono giusti, ma il CRS e'
              assente o dichiarato male.</li>
          <li><b>Reproject</b> crea una copia in un altro CRS trasformando le
              coordinate. Usalo dopo avere assegnato il CRS nativo
              corretto.</li>
          <li>Il plugin salva il risultato in GeoPackage e sostituisce nel
              progetto il layer originale con quello corretto.</li>
        </ul>
        <h3>Deep Scan OSM</h3>
        <ol>
          <li>Seleziona un layer problematico.</li>
          <li>Premi <b>Deep Scan OSM</b>.</li>
          <li>Il plugin cerca un campo testuale utile, interroga Nominatim e
              Wikipedia, poi confronta il centro teorico con una lista di EPSG
              candidati.</li>
          <li>Se vengono trovati piu' EPSG plausibili, scegli quello desiderato
              dal menu a tendina prima di applicare la correzione.</li>
        </ol>
        <h3>Fix All</h3>
        <p><b>Fix All</b> assegna automaticamente il CRS suggerito a tutti i
        layer segnalati. Usalo solo quando i suggerimenti sono coerenti:
        per dati critici e' preferibile controllare layer per layer.</p>
        <h3>Riassegna EPSG</h3>
        <p>La scheda <b>Riassegna EPSG</b> mostra i layer appena sistemati e
        consente una riproiezione finale opzionale verso un EPSG scelto.</p>
        <h3>Controlli pratici</h3>
        <ul>
          <li>Coordinate piccole come 12, 42 indicano spesso EPSG:4326.</li>
          <li>Coordinate UTM italiane hanno spesso X tra 300000 e 800000 e Y
              tra 4000000 e 5300000.</li>
          <li>Gauss-Boaga usa falsi Est intorno a 1500000 o 2520000.</li>
          <li>Deep Scan richiede connessione internet e usa servizi
              esterni.</li>
        </ul>
        """

    def update_list(self, issues_data):
        self.tree.clear()
        self.current_issues = issues_data
        count = 0
        for layer_id, data in issues_data.items():
            count += 1
            parent = QTreeWidgetItem(self.tree)
            parent.setText(0, data["name"])
            parent.setData(0, Qt.ItemDataRole.UserRole, layer_id)
            icon_name = (
                "mIconDelete"
                if data["severity"] == "error"
                else "mIconWarning"
            )
            parent.setIcon(0, QIcon.fromTheme(icon_name))

            for issue in data["issues"]:
                suggestion = data.get("suggestion") or {
                    "name": self.tr("suggest.missing"),
                    "reason": self.tr("suggest.missing"),
                }
                child = QTreeWidgetItem(parent)
                child.setText(0, issue)
                child.setText(1, suggestion["name"])

        self._issue_count = count
        self.stats_label.setText(self.tr("stats.problems", count=count))
        self.btn_fix_all.setEnabled(count > 0)
        self.tree.expandAll()

    def on_selection_changed(self):
        items = self.tree.selectedItems()
        if not items:
            self.toggle_buttons(False)
            self.epsg_combo.hide()
            self.details_label.setText(self.tr("ui.empty_details"))
            return
        item = items[0]
        if item.parent():
            item = item.parent()
        layer_id = item.data(0, Qt.ItemDataRole.UserRole)
        data = self.current_issues.get(layer_id)
        if data:
            suggestion = data.get("suggestion") or {
                "name": self.tr("suggest.missing"),
                "reason": self.tr("suggest.missing"),
            }
            self.details_label.setText(
                f"<b>{data['name']}</b>:<br>{suggestion['reason']}"
            )

            self.epsg_combo.clear()
            if "options" in suggestion:
                for opt in suggestion["options"]:
                    self.epsg_combo.addItem(opt["name"], opt["id"])
                self.epsg_combo.show()
            else:
                self.epsg_combo.hide()

            self.toggle_buttons(True)

    def toggle_buttons(self, enabled):
        self.btn_assign.setEnabled(enabled)
        self.btn_reproject.setEnabled(enabled)
        self.btn_deep_scan.setEnabled(enabled)

    def emit_fix(self, action_type):
        items = self.tree.selectedItems()
        if items:
            item = items[0]
            if item.parent():
                item = item.parent()
            layer_id = item.data(0, Qt.ItemDataRole.UserRole)
            self.fixRequested.emit(layer_id, action_type, "")

    def emit_deep_scan(self):
        items = self.tree.selectedItems()
        if items:
            item = items[0]
            if item.parent():
                item = item.parent()
            layer_id = item.data(0, Qt.ItemDataRole.UserRole)
            self.details_label.setText(self.tr("deep_scan.running"))
            self.deepScanRequested.emit(layer_id, "")
        else:
            self.details_label.setText(self.tr("deep_scan.select_layer"))

    def update_resolved_list(self, resolved_data):
        self.tree_resolved.clear()
        self.resolved_issues = resolved_data
        for layer_id, data in resolved_data.items():
            item = QTreeWidgetItem(self.tree_resolved)
            item.setText(0, data["name"])
            item.setData(0, Qt.ItemDataRole.UserRole, layer_id)
            item.setIcon(0, QIcon.fromTheme("mIconSuccess"))
            item.setText(
                1, data.get("suggestion", {}).get("name", self.tr("valid"))
            )

    def on_resolved_selection_changed(self):
        items = self.tree_resolved.selectedItems()
        if not items:
            self.btn_reproject_resolved.setEnabled(False)
            self.resolved_combo.hide()
            self.resolved_details.setText(self.tr("resolved.empty_details"))
            return
        item = items[0]
        layer_id = item.data(0, Qt.ItemDataRole.UserRole)
        data = self.resolved_issues.get(layer_id)
        if data:
            self.resolved_details.setText(
                self.tr("resolved.details", name=data["name"])
            )
            self.resolved_combo.clear()
            if "options" in data.get("suggestion", {}):
                for opt in data["suggestion"]["options"]:
                    self.resolved_combo.addItem(opt["name"], opt["id"])
                self.resolved_combo.show()
            else:
                self.resolved_combo.addItem(
                    data["suggestion"]["name"], data["suggestion"]["id"]
                )
                self.resolved_combo.show()
            self.btn_reproject_resolved.setEnabled(True)

    def emit_reproject_resolved(self):
        items = self.tree_resolved.selectedItems()
        if items:
            layer_id = items[0].data(0, Qt.ItemDataRole.UserRole)
            self.fixRequested.emit(layer_id, "reproject_resolved", "")
