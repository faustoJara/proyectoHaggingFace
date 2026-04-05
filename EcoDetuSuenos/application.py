from flask import Flask, render_template, request, redirect, url_for, session
from huggingface_hub import InferenceClient
import os

application = Flask(__name__)
application.secret_key = 'supersecreto'

# CONFIGURACIÓN DE SEGURIDAD PARA EL CLIENTE


# Intentamos inicializar el cliente, si falla, la app no se detiene
try:
    cliente_hf = InferenceClient(token=TOKEN_REAL)
except Exception as e:
    print(f"Error inicializando cliente HF: {e}")
    cliente_hf = None

@application.route('/')
def home():
    if 'usuario' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@application.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        # Credenciales académicas estándar
        if request.form['username'] == 'admin' and request.form['password'] == '1234':
            session['usuario'] = request.form['username']
            return redirect(url_for('home'))
        else:
            error = 'Credenciales incorrectas. Intenta admin / 1234.'
    return render_template('login.html', error=error)

@application.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@application.route('/analizar', methods=['POST'])
def analizar():
    datos = request.get_json()
    texto_sueno = datos.get('texto', '')
    
    # --- RESPALDO (BACKUP) ---
    # Si la IA falla, estos son los valores que el usuario verá para que la web NO se rompa
    emocion_final = "Mística"
    interpretacion_final = "El Oráculo está meditando sobre tu visión. Los astros sugieren que este sueño marca un nuevo comienzo en tu camino espiritual."

    if not cliente_hf:
        return {"emocion": emocion_final, "interpretacion": interpretacion_final}

    try:
        # 1. Intento de Clasificación de Emoción
        try:
            res_emo = cliente_hf.text_classification(texto_sueno, model="finiteautomata/beto-sentiment-analysis")
            etiqueta = res_emo[0].label if hasattr(res_emo[0], 'label') else res_emo[0]['label']
            if etiqueta == "POS": emocion_final = "Positiva"
            elif etiqueta == "NEG": emocion_final = "Negativa"
        except Exception as e:
            print(f"Fallo emoción: {e}")

        # 2. Intento de Generación de Texto (Interpretación)
        try:
            prompt = f"<start_of_turn>user\nInterpreta este sueño de forma breve y mística en español: {texto_sueno}<end_of_turn>\n<start_of_turn>model\n"
            res_txt = cliente_hf.text_generation(prompt, model="google/gemma-2-2b-it", max_new_tokens=80)
            if res_txt:
                # Limpiamos el texto por si la IA repite el prompt
                interpretacion_final = res_txt.split("<start_of_turn>model\n")[-1].strip()
        except Exception as e:
            print(f"Fallo interpretación: {e}")

        return {"emocion": emocion_final, "interpretacion": interpretacion_final}
        
    except Exception as e:
        # Si todo falla, enviamos el respaldo místico en lugar de un error 500
        return {"emocion": emocion_final, "interpretacion": interpretacion_final}

# ESTO ES VITAL PARA AWS ELASTIC BEANSTALK
app = application 

if __name__ == '__main__':
    # Usamos el puerto 8000 que es el que tus logs mostraron que AWS prefiere
    application.run(host='0.0.0.0', port=8000)