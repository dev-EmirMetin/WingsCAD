# WingsCAD

Python-based NACA airfoil generation & visualization tool with a modern GUI.

> **WingsCAD** lets you quickly generate, inspect and export NACA airfoil geometries (4-, 5-, 6-, 7- and 8-series) with an interactive, CAD-like interface.

---

## 🖼 Preview

<img width="1919" height="1030" alt="image" src="https://github.com/user-attachments/assets/6c5d4957-ac4a-4cea-8016-9b95f43e4147" />

---

## ✨ Features

- **Multiple NACA families**
  - NACA **4-digit**, **5-digit**, **6-series**, **7-series**, **8-series**
  - Unified GUI: family sekmesi sadece üst şeritte değişiyor, akış bozulmuyor

- **Real-time airfoil preview**
  - Cosine-spaced coordinates for smooth leading edge
  - Upper / lower surface + **camber line** overlay
  - Dark, CAD-style grid (no pure white background)

- **Parametric control**
  - NACA code (e.g. 2412, 23012, 63-018…)
  - Chord length (float)
  - Points per surface (50–2000)

- **Geometry properties panel**
  - Max camber, camber position, thickness
  - Max thickness location, camber magnitude
  - Approx. area and leading-edge radius

- **Export options**
  - **Selig `.dat`** format (x, y)
  - Simple **`.csv`** export (x,y)

- **Modern GUI**
  - Built with **PyQt5/6** and **Matplotlib**
  - Ribbon-style top bar (family, parameters, actions, export, view, properties)
  - Dark theme with grey–blue–red highlight colors
  - Custom icon set designed specifically for WingsCAD

- **Open-source & extensible**
  - Clean separation between **core geometry** (`core/`) and **UI** (`wingscad_ui.py`)
  - Easy to plug new airfoil families or analysis modules

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/dev-EmirMetin/WingsCAD.git
cd WingsCAD
pip install -r requirements.txt
python main.py
Emir Metin
Aerospace Engineering @ Samsun University
Software Lead @ ASTARTE Rocket Team
Erasmus+ 2025/26 @ UPB – Politehnica University of Bucharest
