import asyncio
import logging
import requests
import shlex
import subprocess
import threading
from flask import Flask, request

from src.settings import TELEGRAM_TOKEN, TELEGRAM_CHAT_IDS_FILE, WEBHOOK_DOMAIN
from src.scripts.telegram_bot import IntegrateTelegramBot

logger = logging.getLogger(__name__)

app = Flask(__name__)

telegram_bot = IntegrateTelegramBot()

WEBHOOK_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={WEBHOOK_DOMAIN}"


def save_chat_id(chat_id):
    chat_ids = telegram_bot.load_chat_ids()
    if str(chat_id) not in chat_ids:
        with open(TELEGRAM_CHAT_IDS_FILE, "a") as file:
            file.write(f"{chat_id}\n")
        logger.info(f"Chat ID '{chat_id}' successfuly included.")


def set_webhook():
    response = requests.get(WEBHOOK_URL)
    if response.status_code == 200:
        logger.info("Webhook succesfully configured!")
    else:
        logger.error("Error configuring the webhook:", response.text)


@app.route("/webhook", methods=["POST"])
async def webhook():
    data = request.get_json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        save_chat_id(chat_id)
        received_msg = data.get("message", {}).get("text") or ""
        if received_msg == "/start":
            initial_msg = (
                "📈 GEX Indicator iniciado com sucesso.\n\n"
                "Comandos suportados (individuais ou combinações):\n"
                "  ▶️ --all (calcular todos vencimentos)\n"
                "  ▶️ --zero_dte (calcular apenas 0DTE)\n"
                "  ▶️ --flip_point (considerar flip gamma)\n"
                "  ▶️ --split_visualization (mostrar índices separados)\n"
                "  ▶️ --expiration_month agosto (mês de vencimento)\n"
            )
            await telegram_bot._send_telegram_message(message=initial_msg, chat_id=chat_id)

        def run_and_notify(cmd):
            try:
                logger.info(f"Processing command {cmd}")
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
                for line in process.stdout:
                    print(line, end="", flush=True)
                process.wait()
                if process.returncode == 0:
                    asyncio.run(
                        telegram_bot._send_telegram_message(
                            message="✅ Processo concluído com sucesso!", chat_id=chat_id
                        )
                    )
                else:
                    logger.error(process.stderr.read())
                    asyncio.run(
                        telegram_bot._send_telegram_message(
                            message=f"❌ Erro na execução com o argumento {cmd}.", chat_id=chat_id
                        )
                    )
            except Exception as e:
                asyncio.run(
                    telegram_bot._send_telegram_message(message=f"❌ Falha ao rodar o processo: {e}", chat_id=chat_id)
                )

        msg_to_send = "🚀 Execução iniciada com os parâmetros: {args}.\nAguarde..."
        received_msg = received_msg.replace("—", "--")
        if "--all" in received_msg:
            cmd = ["python", "app.py", "--telegram_chat_id", str(chat_id)]
            threading.Thread(target=run_and_notify, args=(cmd,)).start()

            await telegram_bot._send_telegram_message(
                message=msg_to_send.format(args=" ".join(received_msg)), chat_id=chat_id
            )
        elif "--" in received_msg and "--all" not in received_msg:
            args = shlex.split(received_msg)
            cmd = ["python", "app.py", "--telegram_chat_id", str(chat_id)] + args
            threading.Thread(target=run_and_notify, args=(cmd,)).start()

            await telegram_bot._send_telegram_message(message=msg_to_send.format(args=" ".join(args)), chat_id=chat_id)
        else:
            if "start" not in received_msg:
                await telegram_bot._send_telegram_message(
                    message=f"❌ Comando '{received_msg}' não reconhecido", chat_id=chat_id
                )

    return "OK", 200


if __name__ == "__main__":
    if "http" not in WEBHOOK_DOMAIN:
        raise ValueError(
            "WEBHOOK Domain must be provided by running the command 'ngrok http 5000', "
            "copying the 'Forwarding' URL, and pasting it into 'WEBHOOK_DOMAIN' at your .env file"
        )
    set_webhook()
    app.run(host="0.0.0.0", port=5000)
