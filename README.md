# miniature-giggle

Proyecto de fin de grado: Caracterización del ciclo diurno del tope de nubes de los ciclones tropicales en el Océano Atlántico Norte.

```text
📂 src/
└── 📂 tfg/
    └── 📂 storage/               # Almacenamiento
        ├── 📂 backend/           # Backends de almacenamiento
        │   ├── 📄 base.py        # Protocolo para backends de almacenamiento de datos crudos
        │   ├── 📄 aws.py         # Backend de almacenamiento para Amazon Web Services S3
        │   ├── 📄 filesystem.py  # Backend de almacenamiento para el sistema de archivos local
        │   ├── 📄 gcs.py         # Backend de almacenamiento para Google Cloud Storage
        │   ├── 📄 gdrive.py      # Backend de almacenamiento para Google Drive API v3
        │   └── 📄 ...
        │
        ├── 📂 cache/             # Caché
        │   ├── 📄 base.py        # Protocolos para cachés de almacenamiento de datos
        │   ├── 📄 dummy.py       # Caché genérica tonta que no almacena ningún dato.
        │   ├── 📄 simple.py      # Caché genérica no temporizada
        │   └── 📄 timed.py       # Caché genérica temporizada
        │
        ├── 📂 core/              # Núcleo de coordinación e instanciación
        │   ├── 📄 aws.py         # Crea un Datasource conectado a Amazon Web Services S3
        │   ├── 📄 colab.py       # Crea un Datasource para Google Drive en Google Colab
        │   ├── 📄 gcs.py         # Crea un Datasource conectado a Google Cloud Storage
        │   ├── 📄 gdrive.py      # Crea un Datasource conectado a Google Drive vía API v3
        │   ├── 📄 local.py       # Crea un Datasource conectado al sistema de archivos local
        │   └── 📄 downloader.py  # Crea un Downloader para transferir datos entre dos backends
        │
        ├── 📂 datasource/        # Orquestación de acceso a fuentes de datos
        │   ├── 📄 base.py        # Protocolo para operaciones sobre fuentes de datos
        │   └── 📄 datasource.py  # Contexto que orquesta el acceso a fuentes de datos
        │
        └── 📂 mapper/            # Mapeadores de URI genéricas
            ├── 📄 base.py        # Protocolo para mapeadores de URI genéricas
            ├── 📄 aws.py         # Mapeador de URI genéricas y claves de Amazon Web Services S3
            ├── 📄 gcs.py         # Mapeador de URI genéricas y claves de Google Cloud Storage
            ├── 📄 gdrive.py      # Mapeador de URI genéricas e ID nativos de Google Drive
            ├── 📄 generic.py     # Mapeador de URI genéricas respecto a una ruta base
            ├── 📄 path.py        # Mapeador de URI genéricas y rutas del sistema de archivos
            └── 📄 ...
```
