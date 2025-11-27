from core.naca4 import generate_naca4_full
from core.naca5 import generate_naca5_full
from core.naca6 import generate_naca6_full
from core.naca7 import generate_naca7_full
from core.naca8 import generate_naca8_full

import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFormLayout, QGroupBox, QLabel, QLineEdit, QPushButton,
    QSpinBox, QDoubleSpinBox, QCheckBox, QFileDialog,
    QMessageBox, QTabWidget, QTabBar
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


# ---------- MATPLOTLIB CANVAS WIDGET ----------

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure(tight_layout=True)
        fig.patch.set_facecolor("#181a1f")  # Qt arka planına yakın
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)


# ---------- MAIN WINDOW ----------

class WingsCADMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("WingsCAD – Airfoil Designer")
        self.setWindowIcon(QIcon("assets/icons/wingscad.png"))
        self.resize(1400, 800)

        self.current_airfoil = None  # (x, y)
        self.current_camber = None   # (x_c, y_c)
        self.current_family = "NACA 4-digit"

        self._init_ui()

    # ------ UI CONSTRUCTION ------

    def _init_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Ribbon (üst şerit)
        self._build_ribbon(main_layout)

        # Plot alanı
        self._build_plot_area(main_layout)

        self.statusBar().showMessage("Ready")

    # ---------- RIBBON / ÜST ŞERİT ----------

    def _build_ribbon(self, layout: QVBoxLayout):
        self.ribbon_tabs = QTabWidget()
        self.ribbon_tabs.setTabPosition(QTabWidget.North)
        self.ribbon_tabs.setDocumentMode(True)
        self.ribbon_tabs.setTabShape(QTabWidget.Rounded)

        # Tek tab: NACA
        naca_tab = QWidget()
        naca_layout = QHBoxLayout(naca_tab)
        naca_layout.setContentsMargins(4, 4, 4, 4)
        naca_layout.setSpacing(8)

        # --- Family sekmeleri ---
        family_group = QGroupBox("Family")
        family_group.setMinimumWidth(230)
        family_v = QVBoxLayout(family_group)

        self.family_tabbar = QTabBar()
        self.family_tabbar.addTab("NACA 4-digit")
        self.family_tabbar.addTab("NACA 5-digit")
        self.family_tabbar.addTab("NACA 6-series")
        self.family_tabbar.addTab("NACA 7-series")
        self.family_tabbar.addTab("NACA 8-series")
        self.family_tabbar.setExpanding(False)
        self.family_tabbar.setCurrentIndex(0)
        self.family_tabbar.currentChanged.connect(self._on_family_tab_changed)

        family_v.addWidget(self.family_tabbar)
        naca_layout.addWidget(family_group)

        # --- Parameters ---
        params_group = QGroupBox("Parameters")
        params_form = QFormLayout(params_group)

        self.naca_code_edit = QLineEdit()
        self.naca_code_edit.setPlaceholderText("e.g. 2412")
        params_form.addRow("Code:", self.naca_code_edit)

        self.chord_spin = QDoubleSpinBox()
        self.chord_spin.setRange(0.01, 1000.0)
        self.chord_spin.setDecimals(3)
        self.chord_spin.setSingleStep(0.1)
        self.chord_spin.setValue(1.0)
        params_form.addRow("Chord:", self.chord_spin)

        self.n_points_spin = QSpinBox()
        self.n_points_spin.setRange(50, 2000)
        self.n_points_spin.setValue(200)
        params_form.addRow("Points/surface:", self.n_points_spin)

        naca_layout.addWidget(params_group)

        # --- Actions ---
        actions_group = QGroupBox("Actions")
        actions_v = QVBoxLayout(actions_group)

        self.generate_btn = QPushButton("Generate")
        self.generate_btn.setIcon(QIcon("assets/icons/generate.png"))
        self.generate_btn.setIconSize(QSize(18, 18))
        self.generate_btn.clicked.connect(self._on_generate_clicked)
        self.generate_btn.setMinimumWidth(120)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #1f6feb;
                color: white;
                font-weight: bold;
                padding: 6px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1158c7;
            }
        """)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setIcon(QIcon("assets/icons/reset.png"))
        self.reset_btn.setIconSize(QSize(18, 18))
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #e5534b;
                color: white;
                padding: 6px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c93c35;
            }
        """)

        actions_v.addWidget(self.generate_btn)
        actions_v.addWidget(self.reset_btn)
        actions_v.addStretch()
        naca_layout.addWidget(actions_group)

        # --- Export ---
        export_group = QGroupBox("Export")
        export_v = QVBoxLayout(export_group)

        self.export_dat_btn = QPushButton(".dat (Selig)")
        self.export_dat_btn.setIcon(QIcon("assets/icons/export_dat.png"))
        self.export_dat_btn.setIconSize(QSize(18, 18))
        self.export_dat_btn.clicked.connect(self._export_dat)

        self.export_csv_btn = QPushButton(".csv (x,y)")
        self.export_csv_btn.setIcon(QIcon("assets/icons/export_csv.png"))
        self.export_csv_btn.setIconSize(QSize(18, 18))
        self.export_csv_btn.clicked.connect(self._export_csv)

        export_style = """
            QPushButton {
                background-color: #3b3f46;
                color: #f5f5f5;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4a4f57;
            }
        """
        self.export_dat_btn.setStyleSheet(export_style)
        self.export_csv_btn.setStyleSheet(export_style)

        export_v.addWidget(self.export_dat_btn)
        export_v.addWidget(self.export_csv_btn)
        export_v.addStretch()
        naca_layout.addWidget(export_group)

        # --- View options ---
        view_group = QGroupBox("View")
        view_v = QVBoxLayout(view_group)

        self.show_camber_checkbox = QCheckBox("Show camber line")
        self.show_camber_checkbox.setChecked(True)
        self.show_camber_checkbox.stateChanged.connect(self._update_plot)

        self.grid_checkbox = QCheckBox("Show grid")
        self.grid_checkbox.setChecked(True)
        self.grid_checkbox.stateChanged.connect(self._update_plot)

        view_v.addWidget(self.show_camber_checkbox)
        view_v.addWidget(self.grid_checkbox)
        view_v.addStretch()
        naca_layout.addWidget(view_group)

        # --- Properties ---
        props_group = QGroupBox("Properties")
        props_v = QVBoxLayout(props_group)
        self.properties_label = QLabel("No airfoil generated yet.")
        self.properties_label.setWordWrap(True)
        self.properties_label.setStyleSheet("font-size: 11px;")
        props_v.addWidget(self.properties_label)
        naca_layout.addWidget(props_group)

        self.ribbon_tabs.addTab(naca_tab, "NACA")
        layout.addWidget(self.ribbon_tabs)

    # ---------- PLOT AREA ----------

    def _build_plot_area(self, layout: QVBoxLayout):
        self.canvas = MplCanvas(self)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, 1)

        self._init_plot()

    # ------ PLOT LOGIC ------

    def _style_axes(self, ax):
        """Tek yerden eksen / grid stilini ayarla."""
        # koyu gri arka plan
        ax.set_facecolor("#202225")

        # grid
        if self.grid_checkbox.isChecked():
            ax.grid(
                True,
                color="#3a3f44",
                linestyle="-",
                linewidth=0.7
            )
        else:
            ax.grid(False)

        # eksen çerçevesi
        for spine in ax.spines.values():
            spine.set_edgecolor("#70757d")
            spine.set_linewidth(1.0)

        # tick & label renkleri
        ax.tick_params(colors="#d0d4db")
        ax.xaxis.label.set_color("#d0d4db")
        ax.yaxis.label.set_color("#d0d4db")
        ax.title.set_color("#f5f5f5")

        # watermark (çok hafif)
        ax.text(
            0.5, 0.5, "WingsCAD",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=40,
            color="#ffffff",
            alpha=0.04,
            weight="bold",
        )

    def _init_plot(self):
        ax = self.canvas.ax
        ax.clear()
        self._style_axes(ax)
        ax.set_title("No airfoil generated yet")
        ax.set_xlabel("x (chord)")
        ax.set_ylabel("y")
        ax.set_aspect("equal", adjustable="box")
        self.canvas.draw_idle()

    def _update_plot(self):
        ax = self.canvas.ax
        ax.clear()

        if self.current_airfoil is None:
            # Hiç profil yoksa sadece stil + watermark göster
            self._style_axes(ax)
            ax.set_title("No airfoil generated yet")
            ax.set_xlabel("x (chord)")
            ax.set_ylabel("y")
            ax.set_aspect("equal", adjustable="box")
            self.canvas.draw_idle()
            return

        x, y = self.current_airfoil

        # Stil
        self._style_axes(ax)

        # ---- AIRFOIL ----
        ax.plot(x, y, linewidth=1.8, color="#32a8ff")  # mavi profil

        # ---- CAMBER LINE ----
        if self.current_camber is not None and self.show_camber_checkbox.isChecked():
            x_c, y_c = self.current_camber
            ax.plot(x_c, y_c, linestyle="--", linewidth=1.0, color="#ff7373")  # kırmızı

        ax.set_xlabel("x (chord)")
        ax.set_ylabel("y")
        ax.set_aspect("equal", adjustable="box")
        ax.set_title("Airfoil geometry")

        self.canvas.draw_idle()

    # ------ SIGNAL HANDLERS ------

    def _on_family_tab_changed(self, index: int):
        text = self.family_tabbar.tabText(index)
        self.current_family = text

        if text == "NACA 4-digit":
            self.naca_code_edit.setPlaceholderText("e.g. 2412")
        elif text == "NACA 5-digit":
            self.naca_code_edit.setPlaceholderText("e.g. 23012")
        elif text == "NACA 6-series":
            self.naca_code_edit.setPlaceholderText("e.g. 63-018")
        elif text == "NACA 7-series":
            self.naca_code_edit.setPlaceholderText("7xxx")
        elif text == "NACA 8-series":
            self.naca_code_edit.setPlaceholderText("8xxx")

        self.statusBar().showMessage(f"{text} selected", 3000)

    def _on_generate_clicked(self):
        code = self.naca_code_edit.text().strip()
        chord = float(self.chord_spin.value())
        n_points = int(self.n_points_spin.value())

        if not code:
            QMessageBox.information(
                self,
                "Missing code",
                "Please enter an airfoil code (e.g. 2412, 23012, 63-018...)."
            )
            return

        try:
            fam = self.current_family
            if fam == "NACA 4-digit":
                x, y, x_c, yc, metrics = generate_naca4_full(
                    code, chord=chord, n_points=n_points, spacing="cosine"
                )
            elif fam == "NACA 5-digit":
                x, y, x_c, yc, metrics = generate_naca5_full(
                    code, chord=chord, n_points=n_points, spacing="cosine"
                )
            elif fam == "NACA 6-series":
                x, y, x_c, yc, metrics = generate_naca6_full(
                    code, chord=chord, n_points=n_points, spacing="cosine"
                )
            elif fam == "NACA 7-series":
                x, y, x_c, yc, metrics = generate_naca7_full(
                    code, chord=chord, n_points=n_points, spacing="cosine"
                )
            elif fam == "NACA 8-series":
                x, y, x_c, yc, metrics = generate_naca8_full(
                    code, chord=chord, n_points=n_points, spacing="cosine"
                )
            else:
                QMessageBox.information(
                    self,
                    "Not implemented",
                    f"{fam} not implemented in core."
                )
                return
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate airfoil:\n{e}")
            return

        self.current_airfoil = (x, y)
        self.current_camber = (x_c, yc)

        # Properties text (metrics dict’i varsa)
        if isinstance(metrics, dict):
            props_text = (
                f"Code: {metrics.get('code', code)}\n"
                f"Chord: {metrics.get('chord', chord):.3f}\n"
                f"m (max camber): {metrics.get('m', 0.0):.3f}\n"
                f"p (camber pos.): {metrics.get('p', 0.0):.3f}\n"
                f"t (thickness): {metrics.get('t', 0.0):.3f}\n"
                f"Max thickness: {metrics.get('max_thickness', 0.0):.4f}\n"
                f"Max camber (abs): {metrics.get('max_camber', 0.0):.4f}\n"
                f"Area: {metrics.get('area', 0.0):.4f}\n"
                f"LE radius: {metrics.get('leading_edge_radius', 0.0):.4f}"
            )
        else:
            props_text = f"{self.current_family}\nCode: {code}\nChord: {chord:.3f}"

        self.properties_label.setText(props_text)

        self.statusBar().showMessage(
            f"Generated {self.current_family} {code} with {len(x)} points (chord={chord})",
            5000
        )
        self._update_plot()

    def _on_reset_clicked(self):
        self.naca_code_edit.clear()
        self.chord_spin.setValue(1.0)
        self.n_points_spin.setValue(200)
        self.current_airfoil = None
        self.current_camber = None
        self.properties_label.setText("No airfoil generated yet.")
        self._init_plot()
        self.statusBar().showMessage("Parameters reset", 3000)

    # ------ EXPORT FUNCTIONS ------

    def _export_dat(self):
        if self.current_airfoil is None:
            QMessageBox.information(self, "No data", "There is no airfoil to export.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export .dat file", "", "DAT files (*.dat);;All files (*.*)"
        )
        if not filename:
            return

        x, y = self.current_airfoil

        try:
            with open(filename, "w") as f:
                f.write("Generated by WingsCAD\n")
                for xi, yi in zip(x, y):
                    f.write(f"{xi:.6f} {yi:.6f}\n")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export .dat:\n{e}")
            return

        self.statusBar().showMessage(f"Exported .dat to {filename}", 5000)

    def _export_csv(self):
        if self.current_airfoil is None:
            QMessageBox.information(self, "No data", "There is no airfoil to export.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export .csv file", "", "CSV files (*.csv);;All files (*.*)"
        )
        if not filename:
            return

        x, y = self.current_airfoil

        try:
            with open(filename, "w") as f:
                f.write("x,y\n")
                for xi, yi in zip(x, y):
                    f.write(f"{xi:.6f},{yi:.6f}\n")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export .csv:\n{e}")
            return

        self.statusBar().showMessage(f"Exported .csv to {filename}", 5000)


# ---------- ENTRY POINT ----------

def main():
    app = QApplication(sys.argv)

    # Global dark-ish tema
    app.setStyleSheet("""
        QWidget {
            background-color: #181a1f;
            color: #e4e6eb;
            font-family: "Segoe UI";
            font-size: 9pt;
        }
        QGroupBox {
            border: 1px solid #2c313a;
            border-radius: 4px;
            margin-top: 8px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px 0 4px;
            color: #e4e6eb;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #20232a;
            border: 1px solid #3a3f4b;
            border-radius: 3px;
            padding: 2px 4px;
        }
        QTabWidget::pane {
            border: 0;
        }
        QTabBar::tab {
            background: #20232a;
            padding: 4px 12px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background: #2c313a;
        }
        QCheckBox {
            spacing: 4px;
        }
    """)

    window = WingsCADMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
