import os
import time
import subprocess
from datetime import datetime
from threading import Thread

from flask import Flask, Response, jsonify
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

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


FILE_NAMES = [
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


# ============================================================
# DIRETÓRIOS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

os.makedirs(
    DATA_DIR,
    exist_ok=True
)


collection_name = datetime.now().strftime(
    "coleta_%Y%m%d_%H%M%S"
)

collection_dir = os.path.join(
    DATA_DIR,
    collection_name
)

os.makedirs(
    collection_dir,
    exist_ok=True
)


# ============================================================
# ESTADO
# ============================================================

current_finger = 0
recording = False
finished = False
transfer_status = ""


# ============================================================
# CÂMERA
# ============================================================

picam2 = Picamera2()

config = picam2.create_video_configuration(

    main={
        "size": (1920, 1080),
        "format": "RGB888"
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
# HTML
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
        "Gravando por 3 segundos...";


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


        esperarGravacao();

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


function esperarGravacao() {

    fetch("/status")

    .then(response => response.json())

    .then(data => {

        if (data.recording) {

            setTimeout(
                esperarGravacao,
                200
            );

            return;
        }


        busy = false;

        document.getElementById(
            "status"
        ).innerText =
            "Gravação concluída.";


        atualizarTela(data);


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


function atualizarStatus() {

    fetch("/status")

    .then(response => response.json())

    .then(data => {

        atualizarTela(data);

    });
}


function concluir() {

    if (busy) {

        alert(
            "Aguarde a gravação terminar."
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
# CÂMERA
# ============================================================

@app.route("/camera")
def camera():

    frame = picam2.capture_array()


    success, encoded = cv2.imencode(
        ".jpg",
        frame
    )


    if not success:

        return (
            "Erro ao capturar imagem",
            500
        )


    return Response(
        encoded.tobytes(),
        mimetype="image/jpeg"
    )


# ============================================================
# GRAVAÇÃO DE 3 SEGUNDOS
# ============================================================

def record_video():

    global recording
    global current_finger
    global finished


    finger = FINGERS[
        current_finger
    ]


    filename = "{}_{}.h264".format(
        current_finger + 1,
        FILE_NAMES[current_finger]
    )


    filepath = os.path.join(
        collection_dir,
        filename
    )


    recording = True


    try:

        print()
        print(
            "Gravando:",
            finger
        )


        encoder = H264Encoder(
            bitrate=6000000
        )


        output = FileOutput(
            filepath
        )


        picam2.start_recording(
            encoder,
            output
        )


        # EXATAMENTE 3 SEGUNDOS

        time.sleep(3)


        picam2.stop_recording()


        print(
            "Vídeo salvo:",
            filepath
        )


        current_finger += 1


        if current_finger >= len(FINGERS):

            finished = True


    except Exception as e:

        print(
            "Erro na gravação:",
            e
        )


    finally:

        recording = False


# ============================================================
# CAPTURAR
# ============================================================

@app.route(
    "/capture",
    methods=["POST"]
)
def capture():

    global recording


    if finished:

        return jsonify({
            "error":
                "A coleta já foi finalizada."
        })


    if recording:

        return jsonify({
            "error":
                "Aguarde a gravação terminar."
        })


    if current_finger >= len(FINGERS):

        return jsonify({
            "error":
                "Todos os dedos já foram gravados."
        })


    thread = Thread(
        target=record_video
    )


    thread.start()


    return jsonify({
        "message":
            "Gravando..."
    })


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

        "recording":
            recording,

        "finished":
            finished,

        "collection":
            collection_name

    })


# ============================================================
# TRANSFERÊNCIA
# ============================================================

def transfer_collection():

    global transfer_status


    print()
    print("====================================")
    print("TRANSFERINDO COLETA PARA O PC")
    print("====================================")


    try:

        # Criar pasta no PC

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

            return False


        # Transferir coleta

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


        result = subprocess.run(

            scp_command,

            capture_output=True,

            text=True

        )


        if result.returncode != 0:

            print(
                result.stderr
            )

            transfer_status = (
                "Erro durante a transferência."
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


    if recording:

        return jsonify({

            "message":
                "Aguarde a gravação terminar.",

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
    print("COLETA DE IMPRESSÕES - VÍDEO")
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