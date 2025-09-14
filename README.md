# 📂 FolderChronicle

FolderChronicle is a small desktop app that organizes files into folders by **Year/Month**. It has a simple Tkinter GUI and can optionally make a timestamped backup before moving files.


## ✨ Features

- 🖥️ **User-friendly GUI** – no need for command-line skills.  
- 📅 **Automatic sorting by date** – organizes files into `Year/Month` folders.  
- 📂 **Structured archive** – all your files are neatly placed in corresponding folders.  
- 🔄 **Move or copy** – move files (with optional backup) or copy without backup.  
- ⚡ **Fast and efficient** – handles large directories with ease.  

## 📷 Example

If you select a folder containing:

```
/Downloads
  ├── report.docx (2021-03-10)
  ├── photo.jpg (2020-07-22)
  ├── invoice.pdf (2021-03-15)
  └── notes.txt (2019-11-02)
```

FolderChronicle will transform it into:

```
/Downloads
  ├── 2019
  │    └── 11
  │         └── notes.txt
  ├── 2020
  │    └── 07
  │         └── photo.jpg
  └── 2021
       └── 03
            ├── report.docx
            └── invoice.pdf
```

## ▶️ How to Run

Option A – run from source (Python 3.8+):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
python -m folderchronicle.app
```

Option B – simple script:

```powershell
python folderchronicle.py
```


The UI uses the Adapta ttk theme via the optional `ttkthemes` package. If it's missing, the app falls back to the default `clam` theme.

## 🛠️ Requirements
- Windows (primary); Tkinter also works on macOS/Linux if installed

## 📌 Roadmap

- [ ] Support for custom folder naming formats.  
- [ ] Drag & drop directory support.  
- [ ] Dark mode for the GUI.

## 🤝 Contributing

Contributions are welcome!  
Feel free to fork this repo, submit pull requests, or open issues with feature ideas and bug reports.

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

### 🕰️ Let FolderChronicle turn your chaotic folders into a clear timeline!  
