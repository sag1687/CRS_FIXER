import os
from qgis.gui import QgsDockWidget
from qgis.PyQt.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem,
    QLabel, QWidget, QFrame, QComboBox, QTabWidget
)
from qgis.PyQt.QtCore import Qt, pyqtSignal, QUrl
from qgis.PyQt.QtGui import QIcon, QPixmap, QDesktopServices


class QuickCRSDockWidget(QgsDockWidget):
    fixRequested = pyqtSignal(str, str, str)
    refreshRequested = pyqtSignal()
    deepScanRequested = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super(QuickCRSDockWidget, self).__init__(parent)
        self.setWindowTitle("Quick CRS Fixer")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.current_issues = {}

        self.main_widget = QWidget()
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # UI Styling
        self.main_widget.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #001f3f; /* Navy Blue background */
                color: #ffffff; /* White text for contrast */
            }
            QTreeWidget {
                border: none;
                background-color: #002b5e;
                alternate-background-color: #003870;
                color: #ffffff;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #005a9e;
            }
            QHeaderView::section {
                background-color: #001f3f;
                color: #ffffff;
                border: 1px solid #003870;
                padding: 4px;
            }
            QPushButton {
                background-color: #005a9e;
                color: white;
                border-radius: 0px;
                padding: 8px 12px;
                font-weight: bold;
                border: 1px solid #0078d7;
            }
            QPushButton:hover {
                background-color: #0078d7;
            }
            QPushButton:disabled {
                background-color: #001f3f;
                color: #555555;
                border: 1px solid #333333;
            }
            QLabel {
                color: #ffffff;
            }
            QComboBox, QLineEdit {
                background-color: #005a9e;
                color: white;
                border: 1px solid #0078d7;
                padding: 4px;
            }
            QComboBox QAbstractItemView {
                background-color: #003870;
                color: white;
                selection-background-color: #0078d7;
            }
            QTabWidget::pane {
                border: 1px solid #003870;
            }
            QTabBar::tab {
                background-color: #001f3f;
                color: #ffffff;
                padding: 8px 12px;
                border: 1px solid #003870;
            }
            QTabBar::tab:selected {
                background-color: #005a9e;
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
        self.stats_label = QLabel("<b>Problemi: 0</b>")
        self.stats_label.setStyleSheet("font-size: 14px; color: #ff8c00;")
        self.header_layout.addWidget(self.stats_label)

        self.refresh_btn = QPushButton(
            QIcon.fromTheme('view-refresh'), "Aggiorna")
        self.refresh_btn.setStyleSheet("background-color: #005a9e;")
        self.refresh_btn.clicked.connect(lambda: self.refreshRequested.emit())
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.refresh_btn)
        self.fixer_layout.addWidget(self.header_frame)

        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Layer / Problema", "Suggerimento"])
        self.tree.setColumnWidth(0, 200)
        self.tree.setAlternatingRowColors(True)
        self.fixer_layout.addWidget(self.tree)
        # Details
        self.details_label = QLabel(
            "<i>Seleziona un layer dalla lista per vedere i dettagli...</i>")
        self.details_label.setWordWrap(True)
        self.details_label.setStyleSheet(
            "padding: 8px; background-color: #002b5e; border-top: 1px solid #005a9e;")
        self.fixer_layout.addWidget(self.details_label)

        # Combo per vari EPSG
        self.epsg_combo = QComboBox()
        self.epsg_combo.hide()
        self.fixer_layout.addWidget(self.epsg_combo)

        # Actions
        self.actions_layout = QHBoxLayout()
        self.btn_assign = QPushButton(QIcon.fromTheme('symlink'), "Assign")
        self.btn_reproject = QPushButton(
            QIcon.fromTheme('transform-move'), "Reproject")
        self.btn_deep_scan = QPushButton(
            QIcon.fromTheme('network-wireless'), "Deep Scan OSM")
        self.btn_fix_all = QPushButton(
            QIcon.fromTheme('dialog-ok-apply'), "Fix All")

        for btn in [
                self.btn_assign,
                self.btn_reproject,
                self.btn_deep_scan,
                self.btn_fix_all]:
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
            ["Layer Sistemato", "EPSG Attuale/Suggerito"])
        self.tree_resolved.setColumnWidth(0, 200)
        self.tree_resolved.setAlternatingRowColors(True)
        self.resolved_layout.addWidget(self.tree_resolved)

        self.resolved_details = QLabel(
            "<i>Seleziona un layer sistemato per riproiettarlo...</i>")
        self.resolved_details.setWordWrap(True)
        self.resolved_details.setStyleSheet(
            "padding: 8px; background-color: #002b5e; border-top: 1px solid #005a9e;")
        self.resolved_layout.addWidget(self.resolved_details)

        self.resolved_combo = QComboBox()
        self.resolved_combo.hide()
        self.resolved_layout.addWidget(self.resolved_combo)

        self.btn_reproject_resolved = QPushButton(
            QIcon.fromTheme('transform-move'), "Riproietta in...")
        self.btn_reproject_resolved.setEnabled(False)
        self.resolved_layout.addWidget(self.btn_reproject_resolved)

        # Tab 2: Info
        self.tab_info = QWidget()
        self.info_layout = QVBoxLayout(self.tab_info)
        self.info_layout.setContentsMargins(10, 10, 10, 10)

        # Logo P
        self.logo_p_label = QLabel()
        logo_p_path = os.path.join(
            os.path.dirname(
                os.path.dirname(__file__)),
            'LOGO_P.png')
        if os.path.exists(logo_p_path):
            pixmap_p = QPixmap(logo_p_path)
            self.logo_p_label.setPixmap(
                pixmap_p.scaled(
                    300,
                    300,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation))
        self.logo_p_label.setAlignment(Qt.AlignCenter)
        self.info_layout.addWidget(self.logo_p_label)

        # Logo Author
        self.logo_label = QLabel()
        logo_path = os.path.join(
            os.path.dirname(
                os.path.dirname(__file__)),
            'logo.jpg')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            self.logo_label.setPixmap(
                pixmap.scaled(
                    80,
                    80,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation))
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.info_layout.addWidget(self.logo_label)

        # Info Text
        info_text = """
        <h2 style='color: #ffffff; text-align: center;'>Quick CRS Fixer</h2>
        <p style='text-align: center;'><b>Versione 1.0</b></p>
        <p style='text-align: center;'>Autore: <b>Dott. Sarino Alfonso Grande</b></p>
        <p style='text-align: center;'>Website: <a href='https://sinocloud.it' style='color: #00a2ff;'>sinocloud.it</a></p>
        <p style='text-align: center;'>Email: sino.grande@gmail.com</p>
        """
        self.info_label = QLabel(info_text)
        self.info_label.setOpenExternalLinks(True)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_layout.addWidget(self.info_label)

        # Inizio Licenze e Dati Esterni
        hline1 = QFrame()
        hline1.setFrameShape(QFrame.HLine)
        hline1.setStyleSheet(
            "background-color: #005a9e; margin-top: 10px; margin-bottom: 5px;")
        self.info_layout.addWidget(hline1)

        disclaimer_text = "<p style='text-align: center; font-size: 11px; color: #a0c4ff;'><i>Il plugin richiede una connessione internet attiva.<br>Deep Scan utilizza servizi esterni per l'analisi intelligente.</i></p>"
        self.disclaimer_label = QLabel(disclaimer_text)
        self.disclaimer_label.setAlignment(Qt.AlignCenter)
        self.info_layout.addWidget(self.disclaimer_label)

        self.logos_layout = QHBoxLayout()

        # OSM
        self.osm_layout = QVBoxLayout()
        osm_path = os.path.join(
            os.path.dirname(
                os.path.dirname(__file__)),
            'osm')
        osm_url = QUrl.fromLocalFile(osm_path).toString()
        self.osm_img = QLabel(
            f"<a href='https://www.openstreetmap.org/copyright'><img src='{osm_url}' width='50'></a>")
        self.osm_img.setOpenExternalLinks(True)
        self.osm_img.setAlignment(Qt.AlignCenter)
        self.osm_desc = QLabel(
            "<p style='text-align: center; font-size: 10px; color: #ffffff;'><b>OpenStreetMap</b><br>Ricerca Geografica<br>Licenza: ODbL</p>")
        self.osm_desc.setAlignment(Qt.AlignCenter)
        self.osm_layout.addWidget(self.osm_img)
        self.osm_layout.addWidget(self.osm_desc)

        # VLine
        vline = QFrame()
        vline.setFrameShape(QFrame.VLine)
        vline.setStyleSheet("background-color: #005a9e;")

        # Wikipedia
        self.wiki_layout = QVBoxLayout()
        wiki_path = os.path.join(
            os.path.dirname(
                os.path.dirname(__file__)),
            'Wikipedia-logo-v2.svg.png')
        wiki_url = QUrl.fromLocalFile(wiki_path).toString()
        self.wiki_img = QLabel(
            f"<a href='https://it.wikipedia.org/'><img src='{wiki_url}' width='50'></a>")
        self.wiki_img.setOpenExternalLinks(True)
        self.wiki_img.setAlignment(Qt.AlignCenter)
        self.wiki_desc = QLabel(
            "<p style='text-align: center; font-size: 10px; color: #ffffff;'><b>Wikipedia</b><br>Informazioni Luoghi<br>Licenza: CC BY-SA</p>")
        self.wiki_desc.setAlignment(Qt.AlignCenter)
        self.wiki_layout.addWidget(self.wiki_img)
        self.wiki_layout.addWidget(self.wiki_desc)

        self.logos_layout.addLayout(self.osm_layout)
        self.logos_layout.addWidget(vline)
        self.logos_layout.addLayout(self.wiki_layout)
        self.info_layout.addLayout(self.logos_layout)

        hline2 = QFrame()
        hline2.setFrameShape(QFrame.HLine)
        hline2.setStyleSheet(
            "background-color: #005a9e; margin-top: 5px; margin-bottom: 10px;")
        self.info_layout.addWidget(hline2)
        # Fine Licenze e Dati Esterni

        # Altri Plugin
        self.info_layout.addWidget(QLabel("<b>Altri Plugin:</b>"))
        self.plugins_combo = QComboBox()
        self.plugins_combo.addItem("Seleziona un plugin...")

        icon_plugin_path = os.path.join(
            os.path.dirname(
                os.path.dirname(__file__)),
            'logoplugin.jpg')
        if os.path.exists(icon_plugin_path):
            self.plugins_combo.addItem(
                QIcon(icon_plugin_path),
                "QGIS_ledger",
                "https://plugins.qgis.org/plugins/qgis_ledger/#plugin-details")
        else:
            self.plugins_combo.addItem(
                "QGIS_ledger",
                "https://plugins.qgis.org/plugins/qgis_ledger/#plugin-details")

        self.plugins_combo.currentIndexChanged.connect(self.open_plugin_link)
        self.info_layout.addWidget(self.plugins_combo)
        self.info_layout.addStretch()

        self.tabs.addTab(self.tab_fixer, "Problemi Rilevati")
        self.tabs.addTab(self.tab_resolved, "Riassegna EPSG")
        self.tabs.addTab(self.tab_info, "Info")

        self.setWidget(self.main_widget)

        self.tree_resolved.itemSelectionChanged.connect(
            self.on_resolved_selection_changed)
        self.btn_reproject_resolved.clicked.connect(
            self.emit_reproject_resolved)
        self.resolved_issues = {}
        self.tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.btn_assign.clicked.connect(lambda: self.emit_fix('assign'))
        self.btn_reproject.clicked.connect(lambda: self.emit_fix('reproject'))
        self.btn_deep_scan.clicked.connect(self.emit_deep_scan)
        self.btn_fix_all.clicked.connect(
            lambda: self.fixRequested.emit(
                'all', 'fix_all', ''))

    def open_plugin_link(self, index):
        url = self.plugins_combo.itemData(index)
        if url:
            QDesktopServices.openUrl(QUrl(url))
            self.plugins_combo.setCurrentIndex(0)

    def update_list(self, issues_data):
        self.tree.clear()
        self.current_issues = issues_data
        count = 0
        for layer_id, data in issues_data.items():
            count += 1
            parent = QTreeWidgetItem(self.tree)
            parent.setText(0, data['name'])
            parent.setData(0, Qt.UserRole, layer_id)
            icon_name = 'mIconDelete' if data['severity'] == 'error' else 'mIconWarning'
            parent.setIcon(0, QIcon.fromTheme(icon_name))

            for issue in data['issues']:
                child = QTreeWidgetItem(parent)
                child.setText(0, issue)
                child.setText(1, data['suggestion']['name'])

        self.stats_label.setText(f"<b>Problemi: {count}</b>")
        self.btn_fix_all.setEnabled(count > 0)
        self.tree.expandAll()

    def on_selection_changed(self):
        items = self.tree.selectedItems()
        if not items:
            self.toggle_buttons(False)
            self.epsg_combo.hide()
            return
        item = items[0]
        if item.parent():
            item = item.parent()
        layer_id = item.data(0, Qt.UserRole)
        data = self.current_issues.get(layer_id)
        if data:
            self.details_label.setText(
                f"<b>{data['name']}</b>:<br>{data['suggestion']['reason']}")

            self.epsg_combo.clear()
            if 'options' in data['suggestion']:
                for opt in data['suggestion']['options']:
                    self.epsg_combo.addItem(opt['name'], opt['id'])
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
            layer_id = item.data(0, Qt.UserRole)
            self.fixRequested.emit(layer_id, action_type, '')

    def emit_deep_scan(self):
        items = self.tree.selectedItems()
        if items:
            item = items[0]
            if item.parent():
                item = item.parent()
            layer_id = item.data(0, Qt.UserRole)
            self.details_label.setText(
                "<i>Ricerca Nominatim/OSM in corso... attendere...</i>")
            self.deepScanRequested.emit(layer_id, "")
        else:
            self.details_label.setText(
                "<b style='color:#ff8c00;'>Seleziona prima un layer dalla lista per indicare a chi applicare l'EPSG individuato!</b>")

    def update_resolved_list(self, resolved_data):
        self.tree_resolved.clear()
        self.resolved_issues = resolved_data
        for layer_id, data in resolved_data.items():
            item = QTreeWidgetItem(self.tree_resolved)
            item.setText(0, data['name'])
            item.setData(0, Qt.UserRole, layer_id)
            item.setIcon(0, QIcon.fromTheme('mIconSuccess'))
            item.setText(1, data.get('suggestion', {}).get('name', 'Valido'))

    def on_resolved_selection_changed(self):
        items = self.tree_resolved.selectedItems()
        if not items:
            self.btn_reproject_resolved.setEnabled(False)
            self.resolved_combo.hide()
            return
        item = items[0]
        layer_id = item.data(0, Qt.UserRole)
        data = self.resolved_issues.get(layer_id)
        if data:
            self.resolved_details.setText(
                f"<b>{data['name']}</b>: Pronto per la riproiezione finale (opzionale).")
            self.resolved_combo.clear()
            if 'options' in data.get('suggestion', {}):
                for opt in data['suggestion']['options']:
                    self.resolved_combo.addItem(opt['name'], opt['id'])
                self.resolved_combo.show()
            else:
                self.resolved_combo.addItem(
                    data['suggestion']['name'], data['suggestion']['id'])
                self.resolved_combo.show()
            self.btn_reproject_resolved.setEnabled(True)

    def emit_reproject_resolved(self):
        items = self.tree_resolved.selectedItems()
        if items:
            layer_id = items[0].data(0, Qt.UserRole)
            self.fixRequested.emit(layer_id, 'reproject_resolved', '')
