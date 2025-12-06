# RPA Carta de Anuência

## Instalação

1.  **Crie um ambiente virtual (recomendado):**

    ```bash
    python -m venv .venv
    ```

2.  **Ative o ambiente virtual:**

    ```bash
    activate_venv() {
        if [[ $(uname) == "Darwin" ]]; then
            source .venv/bin/activate
        elif [[ $(uname) == "Linux" ]]; then
            source .venv/bin/activate
        elif [[ $(uname) == CYGWIN* || $(uname) == MINGW* ]]; then
            source .venv/Scripts/activate
        else
            echo "Unsupported operating system"
        fi
    }

    activate_venv
    ```

3.  **Instale as dependências:**

    ```bash
    pip install poetry
    poetry install
    ```

4.  **Execute o projeto:**

    ```bash
    python main.py
    ```