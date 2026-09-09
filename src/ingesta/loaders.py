from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
import os


DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data"
)


def load_single_pdf(pdf_path: str) -> list:
    print(f"Cargando PDF: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    print(f"Total de páginas cargadas: {len(documents)}")
    return documents


def load_directory(directory: str = None) -> list:
    if directory is None:
        directory = DATA_DIR

    print(f"Escaneando directorio: {directory}")

    if not os.path.exists(directory):
        print(f"Directorio no encontrado: {directory}")
        return []

    loader = DirectoryLoader(
        directory,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True
    )

    documents = loader.load()

    if not documents:
        print("No se encontraron archivos PDF en el directorio.")
        return []

    print(f"Total de páginas cargadas: {len(documents)}")
    return documents


def load_from_github(repo_url: str) -> list:
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        print(f"Clonando repositorio: {repo_url}")
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, tmp_dir],
            check=True,
            capture_output=True
        )

        pdf_files = []
        for root, dirs, files in os.walk(tmp_dir):
            for file in files:
                if file.lower().endswith(".pdf"):
                    pdf_files.append(os.path.join(root, file))

        if not pdf_files:
            raise FileNotFoundError("No se encontraron archivos PDF en el repositorio.")

        print(f"Archivos PDF encontrados: {len(pdf_files)}")

        all_documents = []
        for pdf_path in pdf_files:
            print(f"\nProcesando: {os.path.basename(pdf_path)}")
            documents = load_single_pdf(pdf_path)
            all_documents.extend(documents)

        return all_documents
