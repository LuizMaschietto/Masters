import os
import time
import subprocess
from datetime import datetime

from flask import Flask, Response, jsonify
from picamera2 import Picamera2
import cv2


# ============================================================
# CONFIGURAÇÕES DO PC
# ============================================================

PC_USER = "SEU_USUARIO_PC"
PC_IP = "192.168.50.1"
PC_DESTINO = "/home/SEU_USUARIO_PC/infant_reader/coletas"


# ============================================================
# SEQUÊNCIA DOS DEDOS
# ============================================================

FINGERS = [
    "polegar direito",
    "indicador direito",
    "médio direito",
    "anelar direito",
    "mínimo direito",
    "polegar esquerdo",
    "indicador esquerdo",
    "médio esquerdo",
    "anelar esquerdo",
    "mínimo esquerdo"
]


# ============================================================
# DIRETÓRIOS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

os.makedirs(DATA_DIR, exist_ok=True)


collection_name = datetime.now().strftime(
    "coleta_%Y%m%d_%H%M%S"
)

collection_dir = os.path.join(
    DATA_DIR,
    collection_name
)

os.makedirs(collection_dir, exist_ok=True)


# ============================================================
# ESTADO DA COLETA
# ============================================================

current_finger = 0
capturing = False
finished = False
transfer_status = ""


# ============================================================
# CÂMERA
# ============================================================

picam2 = Picamera2()

config = picam2.create_still_configuration(

    main={
        "size": (3280, 2464),
        "format": "RGB888"
    },

    lores={
        "size": (960, 720),
        "format": "YUV420"
    }
)

picam2.configure(config)

picam2.start()

time.sleep(2)


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)


# ============================================================
# INTERFACE HTML
# ============================================================

HTML = """
<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Coleta de Impressões</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f2f2f2;
    text-align: center;
}

header {
    background: #222;
    color: white;
    padding: 20px;
}

header h1 {
    margin: 0;
    font-size: 32px;
}

#progress {
    font-size: 22px;
    margin-top: 8px;
}

main {
    padding: 25px;
}

#instruction {
    font-size: 36px;
    font-weight: bold;
    margin: 15px;
}

#camera {
    width: 800px;
    max-width: 90vw;
    border: 3px solid #222;
    background: black;
}

#status {
    font-size: 24px;
    margin: 20px;
    min-height: 30px;
}

button {
    border: none;
    border-radius: 10px;
    cursor: pointer;
    font-weight: bold;
}

#captureButton {
    display: block;
    margin: 20px auto;
    width: 320px;
    height: 90px;
    font-size: 32px;
    background: #333;
    color: white;
}

#captureButton:disabled {
    background: #888;
    cursor: not-allowed;
}

#finishButton {
    margin-top: 10px;
    padding: 15px 30px;
    font-size: 20px;
    background: #ddd;
    color: #222;
}

#transfer {
    font-size: 24px;
    font-weight: bold;
    margin: 20px;
}

.hidden {
    display: none;
}

</style>

</head>


<body>

<header>

<h1>Coleta de Impressões Digitais</h1>

<div id="progress">
    Dedo 1 de 10
</div>

</header>


<main>

<div id="instruction">
    Coloque o polegar direito
</div>


<img
    id="camera"
    src="/camera"
>


<div id="status">
    Posicione o dedo e pressione CAPTURAR.
</div>


<button
    id="captureButton"
    onclick="capturar()"
>
    CAPTURAR
</button>


<button
    id="finishButton"
    onclick="concluir()"
>
    CONCLUÍDO
</button>


<div id="transfer"></div>

</main>


<script>

let busy = false;


function falar(texto) {

    if (!("speechSynthesis" in window)) {
        return;
    }

    speechSynthesis.cancel();

    const mensagem =
        new SpeechSynthesisUtterance(texto);

    mensagem.lang = "pt-BR";

    mensagem.rate = 0.9;

    speechSynthesis.speak(mensagem);
}


function atualizarTela(data) {

    if (data.finished) {

        document.getElementById(
            "instruction"
        ).innerText = "Coleta finalizada";

        document.getElementById(
            "progress"
        ).innerText = "Coleta concluída";

        document.getElementById(
            "captureButton"
        ).disabled = true;

        return;
    }


    const numero =
        data.current_finger + 1;


    document.getElementById(
        "progress"
    ).innerText =
        "Dedo " + numero + " de " + data.total;


    document.getElementById(
        "instruction"
    ).innerText =
        "Coloque o " + data.finger;
}


function capturar() {

    if (busy) {
        return;
    }

    busy = true;

    document.getElementById(
        "captureButton"
    ).disabled = true;


    document.getElementById(
        "status"
    ).innerText =
        "Capturando impressão...";


    fetch(
        "/capture",
        {
            method: "POST"
        }
    )

    .then(response => response.json())

    .then(data => {

        if (data.error) {

            document.getElementById(
                "status"
            ).innerText =
                data.error;

            busy = false;

            document.getElementById(
                "captureButton"
            ).disabled = false;

            return;
        }


        document.getElementById(
            "status"
        ).innerText =
            data.message;


        atualizarStatus();

    })

    .catch(error => {

        document.getElementById(
            "status"
        ).innerText =
            "Erro de comunicação.";

        busy = false;

        document.getElementById(
            "captureButton"
        ).disabled = false;

    });
}


function atualizarStatus() {

    fetch("/status")

    .then(response => response.json())

    .then(data => {

        atualizarTela(data);

        busy = false;

        if (!data.finished) {

            document.getElementById(
                "captureButton"
            ).disabled = false;

            const texto =
                "Coloque o " + data.finger;

            falar(texto);
        }

    });
}


function concluir() {

    if (busy) {

        alert(
            "Aguarde a captura terminar."
        );

        return;
    }


    const confirmar = confirm(
        "Deseja finalizar a coleta e transferir os arquivos para o computador?"
    );


    if (!confirmar) {
        return;
    }


    document.getElementById(
        "captureButton"
    ).disabled = true;


    document.getElementById(
        "finishButton"
    ).disabled = true;


    document.getElementById(
        "status"
    ).innerText =
        "Transferindo coleta para o computador...";


    fetch(
        "/finish",
        {
            method: "POST"
        }
    )

    .then(response => response.json())

    .then(data => {

        document.getElementById(
            "status"
        ).innerText =
            data.message;


        document.getElementById(
            "transfer"
        ).innerText =
            data.transfer_status;

    })

    .catch(error => {

        document.getElementById(
            "status"
        ).innerText =
            "Erro durante a transferência.";

    });
}


window.onload = function() {

    fetch("/status")

    .then(response => response.json())

    .then(data => {

        atualizarTela(data);

        if (!data.finished) {

            falar(
                "Coloque o " + data.finger
            );
        }

    });

};

</script>

</body>

</html>
"""


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route("/")
def index():

    return HTML


# ============================================================
# CÂMERA AO VIVO
# ============================================================

@app.route("/camera")
def camera():

    frame = picam2.capture_array("lores")

    frame = cv2.cvtColor(
        frame,
        cv2.COLOR_YUV420p2RGB
    )

    success, encoded = cv2.imencode(
        ".jpg",
        frame
    )

    if not success:
        return "Erro ao capturar imagem", 500


    return Response(
        encoded.tobytes(),
        mimetype="image/jpeg"
    )


# ============================================================
# CAPTURA DA FOTO
# ============================================================

@app.route(
    "/capture",
    methods=["POST"]
)
def capture():

    global current_finger
    global capturing
    global finished


    if finished:

        return jsonify({
            "error":
                "A coleta já foi finalizada."
        })


    if capturing:

        return jsonify({
            "error":
                "Aguarde a captura terminar."
        })


    if current_finger >= len(FINGERS):

        finished = True

        return jsonify({
            "error":
                "Todos os dedos já foram capturados."
        })


    capturing = True


    finger = FINGERS[current_finger]


    # Nome do arquivo sem acentos
    file_names = [
        "polegar_direito",
        "indicador_direito",
        "medio_direito",
        "anelar_direito",
        "minimo_direito",
        "polegar_esquerdo",
        "indicador_esquerdo",
        "medio_esquerdo",
        "anelar_esquerdo",
        "minimo_esquerdo"
    ]


    file_name = "{}_{}.jpg".format(
        current_finger + 1,
        file_names[current_finger]
    )


    filepath = os.path.join(
        collection_dir,
        file_name
    )


    try:

        print(
            "Capturando:",
            finger
        )


        picam2.capture_file(
            filepath
        )


        print(
            "Salvo:",
            filepath
        )


        current_finger += 1


        if current_finger >= len(FINGERS):

            finished = True

            message = (
                "Todos os dedos foram capturados."
            )

        else:

            next_finger = FINGERS[
                current_finger
            ]

            message = (
                finger.capitalize()
                + " capturado. "
                + "Prepare o "
                + next_finger
                + "."
            )


        return jsonify({
            "message": message
        })


    except Exception as e:

        print(
            "Erro:",
            e
        )


        return jsonify({
            "error": str(e)
        }), 500


    finally:

        capturing = False


# ============================================================
# STATUS
# ============================================================

@app.route("/status")
def status():

    if current_finger < len(FINGERS):

        finger = FINGERS[
            current_finger
        ]

    else:

        finger = "todos os dedos"


    return jsonify({

        "current_finger":
            current_finger,

        "total":
            len(FINGERS),

        "finger":
            finger,

        "finished":
            finished,

        "collection":
            collection_name
    })


# ============================================================
# TRANSFERIR PARA O PC
# ============================================================

def transfer_collection():

    global transfer_status


    print()
    print("====================================")
    print("TRANSFERINDO COLETA PARA O PC")
    print("====================================")


    try:

        # Criar diretório no PC

        mkdir_command = [

            "ssh",

            "{}@{}".format(
                PC_USER,
                PC_IP
            ),

            "mkdir",
            "-p",
            PC_DESTINO

        ]


        result = subprocess.run(

            mkdir_command,

            capture_output=True,

            text=True

        )


        if result.returncode != 0:

            transfer_status = (
                "Não foi possível preparar "
                "a pasta no computador."
            )

            print(
                result.stderr
            )

            return False


        # Transferência

        remote_destination = (
            "{}@{}:{}".format(
                PC_USER,
                PC_IP,
                PC_DESTINO
            )
        )


        scp_command = [

            "scp",

            "-r",

            collection_dir,

            remote_destination

        ]


        print(
            "Enviando:",
            collection_dir
        )


        result = subprocess.run(

            scp_command,

            capture_output=True,

            text=True

        )


        if result.returncode != 0:

            transfer_status = (
                "Erro durante a transferência."
            )

            print(
                result.stderr
            )

            return False


        transfer_status = (
            "✓ Arquivos transferidos "
            "para o computador."
        )


        print(
            "TRANSFERÊNCIA CONCLUÍDA"
        )


        return True


    except Exception as e:

        transfer_status = (
            "Erro durante a transferência: "
            + str(e)
        )

        print(
            "Erro:",
            e
        )

        return False


# ============================================================
# CONCLUÍDO
# ============================================================

@app.route(
    "/finish",
    methods=["POST"]
)
def finish():

    global finished


    if capturing:

        return jsonify({

            "message":
                "Aguarde a captura terminar.",

            "transfer_status":
                "Transferência não iniciada."

        })


    finished = True


    success = transfer_collection()


    if success:

        message = (
            "Coleta concluída."
        )

    else:

        message = (
            "A coleta foi finalizada, "
            "mas houve um erro na transferência."
        )


    return jsonify({

        "message":
            message,

        "transfer_status":
            transfer_status

    })


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    print()
    print("====================================")
    print("COLETA DE IMPRESSÕES - FOTO")
    print("====================================")
    print()
    print(
        "Pasta da coleta:",
        collection_dir
    )
    print()
    print(
        "Servidor iniciado."
    )
    print()


    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )