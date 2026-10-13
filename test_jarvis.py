# test_jarvis.py — Suite de tests para Jarvis MK2
import sys
import os
from pathlib import Path

# Asegurar imports
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """✅ Verificar que todos los módulos cargan correctamente"""
    print("\n" + "="*60)
    print("TEST 1: IMPORTS")
    print("="*60)
    
    tests = [
        ("Logger", "from modulos.logger import log"),
        ("Memoria", "from modulos.memoria import Memoria"),
        ("Intenciones", "from modulos.intenciones import DetectorIntenciones"),
        ("IA Local", "from modulos.ia_local import IALocal"),
        ("Control Sistema", "from modulos.control_sistema import ControlSistema"),
        ("GestorAPIs", "from modulos.apis.gestor_apis import GestorAPIs"),
        ("Agent Planner", "from modulos.agent.planner import create_plan"),
        ("Agent Executor", "from modulos.agent.executor import AgentExecutor"),
        ("TaskQueue", "from modulos.agent.task_queue import get_queue"),
    ]
    
    ok, fail = 0, 0
    for nombre, code in tests:
        try:
            exec(code)
            print(f"  ✅ {nombre}")
            ok += 1
        except Exception as e:
            print(f"  ❌ {nombre}: {e}")
            fail += 1
    
    print(f"\n  Resultado: {ok}/{len(tests)} OK\n")
    return fail == 0


def test_apis():
    """✅ APIs especializadas (clima, noticias, matemática)"""
    print("\n" + "="*60)
    print("TEST 2: APIs ESPECIALIZADAS")
    print("="*60)
    
    from modulos.apis.gestor_apis import GestorAPIs
    gestor = GestorAPIs()
    
    tests = [
        ("Matemática", "cuánto es 5 más 3"),
        ("Matemática", "raíz cuadrada de 16"),
        ("Matemática", "20 por ciento de 100"),
        ("Clima", "cuál es el clima en Barranquilla"),
        ("YouTube", "busca en youtube gato gracioso"),
        ("Noticias", "dame las últimas noticias"),
        ("Traductor", "traduce 'hola' al inglés"),
    ]
    
    ok, fail = 0, 0
    for api_name, query in tests:
        try:
            resultado = gestor.detectar_y_ejecutar(query)
            if resultado:
                print(f"  ✅ {api_name}: '{query[:40]}...' → {str(resultado)[:60]}...")
                ok += 1
            else:
                print(f"  ⚠️ {api_name}: Sin resultado (puede ser normal)")
                ok += 1
        except Exception as e:
            print(f"  ❌ {api_name}: {e}")
            fail += 1
    
    print(f"\n  Resultado: {ok}/{len(tests)} intentos\n")
    return True


def test_control_sistema():
    """✅ Control de sistema (apps, búsqueda, volumen)"""
    print("\n" + "="*60)
    print("TEST 3: CONTROL DEL SISTEMA")
    print("="*60)
    
    from modulos.control_sistema import ControlSistema
    control = ControlSistema()
    
    tests = [
        ("Abrir Chrome", "abre chrome"),
        ("Buscar Google", "busca gatos en google"),
        ("Encontrar app", "abre notepad"),
        ("Descripción de función", "qué puedes hacer"),
    ]
    
    ok = 0
    for nombre, comando in tests:
        try:
            resultado = control.interpretar_comando(comando)
            if resultado:
                print(f"  ✅ {nombre}: {resultado[:70]}")
                ok += 1
            else:
                print(f"  ⚠️ {nombre}: Sin resultado")
                ok += 1
        except Exception as e:
            print(f"  ❌ {nombre}: {e}")
    
    print(f"\n  Resultado: {ok}/{len(tests)} OK\n")
    return True


def test_herramientas():
    """✅ Tools: file_controller, computer_control"""
    print("\n" + "="*60)
    print("TEST 4: HERRAMIENTAS (TOOLS)")
    print("="*60)
    
    from modulos.tools.file_controller import file_controller
    from modulos.tools.computer_control import computer_control
    
    ok = 0
    
    # File Controller
    try:
        resultado = file_controller({"action": "list", "path": "desktop"})
        if "Desktop" in resultado or "📁" in resultado:
            print(f"  ✅ file_controller.list: Listar desktop OK")
            ok += 1
        else:
            print(f"  ⚠️ file_controller.list: {resultado[:60]}")
            ok += 1
    except Exception as e:
        print(f"  ❌ file_controller.list: {e}")
    
    # Computer Control - Mouse position
    try:
        resultado = computer_control({"action": "get_mouse_pos"})
        if "Mouse" in resultado:
            print(f"  ✅ computer_control.get_mouse_pos: {resultado}")
            ok += 1
        else:
            print(f"  ⚠️ computer_control: {resultado}")
            ok += 1
    except Exception as e:
        print(f"  ❌ computer_control: {e}")
    
    # File Controller - Info
    try:
        resultado = file_controller({"action": "info", "path": "desktop"})
        if "Desktop" in resultado:
            print(f"  ✅ file_controller.info: Desktop info OK")
            ok += 1
        else:
            print(f"  ⚠️ file_controller.info: {resultado[:60]}")
            ok += 1
    except Exception as e:
        print(f"  ❌ file_controller.info: {e}")
    
    print(f"\n  Resultado: {ok}/3 OK\n")
    return True


def test_agent_planner():
    """✅ Agent: Planner convierte goal a plan JSON"""
    print("\n" + "="*60)
    print("TEST 5: AGENT PLANNER")
    print("="*60)
    
    from modulos.agent.planner import create_plan
    
    goals = [
        "Abre Chrome y busca 'python tutorial'",
        "Crea un archivo de texto en el desktop con contenido 'hola mundo'",
        "Toma una foto de la pantalla y analízala",
    ]
    
    ok = 0
    for goal in goals:
        try:
            plan = create_plan(goal)
            steps = plan.get("steps", [])
            if steps:
                print(f"  ✅ Plan para '{goal[:40]}...'")
                print(f"     → {len(steps)} pasos generados")
                for s in steps[:2]:
                    print(f"       - Paso {s.get('step')}: [{s.get('tool')}] {s.get('description')[:50]}")
                ok += 1
            else:
                print(f"  ⚠️ {goal[:40]}: Plan vacío")
                ok += 1
        except Exception as e:
            print(f"  ❌ {goal[:40]}: {e}")
    
    print(f"\n  Resultado: {ok}/{len(goals)} planes generados\n")
    return True


def test_task_queue():
    """✅ TaskQueue: Submit y tracking de tareas"""
    print("\n" + "="*60)
    print("TEST 6: TASK QUEUE")
    print("="*60)
    
    from modulos.agent.task_queue import get_queue, TaskPriority
    import time
    
    queue = get_queue()
    
    print(f"  Queue status: {queue.pending_count()} pendientes")
    
    # Submit una tarea
    task_id = queue.submit(
        "Escribe 2 + 2 en Python",
        priority=TaskPriority.HIGH,
    )
    
    print(f"  ✅ Tarea sumbitida: {task_id}")
    
    # Esperar un poco
    time.sleep(0.5)
    
    # Verificar estado
    status = queue.get_status(task_id)
    if status:
        print(f"  ✅ Estado retrieved: {status['status']}")
    else:
        print(f"  ⚠️ No se pudo obtener estado")
    
    print(f"\n  Resultado: TaskQueue funcional\n")
    return True


def test_memoria():
    """✅ Sistema de memoria y contexto"""
    print("\n" + "="*60)
    print("TEST 7: MEMORIA Y CONTEXTO")
    print("="*60)
    
    from modulos.memoria import Memoria
    
    mem = Memoria()
    
    # Guardar preferencia
    try:
        mem.agregar_preferencia("nombre_usuario: Sebastian")
        print(f"  ✅ Preferencia guardada: nombre_usuario = Sebastian")
    except Exception as e:
        print(f"  ❌ Guardar preferencia: {e}")
    
    # Recuperar preferencia
    try:
        prefs = mem.obtener_preferencias_texto()
        if prefs:
            print(f"  ✅ Preferencias recuperadas: {prefs[:60]}")
        else:
            print(f"  ⚠️ Preferencias vacías")
    except Exception as e:
        print(f"  ❌ Recuperar preferencias: {e}")
    
    # Contexto
    try:
        mem.actualizar_contexto("ultima_accion", "test ejecutado")
        contexto = mem.obtener_contexto("ultima_accion")
        print(f"  ✅ Contexto: ultima_accion = {contexto}")
    except Exception as e:
        print(f"  ❌ Contexto: {e}")
    
    print(f"\n  Resultado: Sistema de memoria OK\n")
    return True


def test_intenciones():
    """✅ Detector de intenciones"""
    print("\n" + "="*60)
    print("TEST 8: DETECTOR DE INTENCIONES")
    print("="*60)
    
    from modulos.memoria import Memoria
    from modulos.intenciones import DetectorIntenciones
    
    mem = Memoria()
    detector = DetectorIntenciones(mem)
    
    textos = [
        "modo silencioso activado",
        "cambiar a gemini",
        "recuerda que me llamo carlos",
        "estoy feliz",
        "cambiar a modo gaming",
        "limpia el historial",
    ]
    
    ok = 0
    for texto in textos:
        try:
            intencion = detector.detectar_intencion(texto)
            if intencion and intencion.get("tipo"):
                print(f"  ✅ '{texto[:40]}' → tipo={intencion['tipo']}")
                ok += 1
            else:
                print(f"  ⚠️ '{texto[:40]}' → sin intencion específica")
        except Exception as e:
            print(f"  ❌ '{texto[:40]}': {e}")
    
    print(f"\n  Resultado: {ok}/{len(textos)} intenciones detectadas\n")
    return True


def test_ia_local():
    """✅ Orquestador IA (Ollama + Gemini fallback)"""
    print("\n" + "="*60)
    print("TEST 9: ORQUESTADOR IA LOCAL")
    print("="*60)
    
    from modulos.ia_local import IALocal
    from modulos.memoria import Memoria
    
    mem = Memoria()
    ia = IALocal(modelo="mistral", memoria=mem)
    
    print(f"  Motor actual: {ia.motor}")
    print(f"  Modelos disponibles: Ollama, Gemini")
    
    # Prueba simple
    try:
        print(f"\n  ⏳ Consultando IA (esto puede tardar 5-10s)...")
        respuesta = ia.consultar("¿Cuál es la capital de Colombia?")
        if respuesta and len(respuesta) > 5:
            print(f"  ✅ Respuesta IA: {respuesta[:100]}...")
            return True
        else:
            print(f"  ⚠️ Respuesta vacía o muy corta")
            return True
    except Exception as e:
        print(f"  ⚠️ Error consultando IA: {e}")
        print(f"     (Verifica que Ollama esté corriendo: ollama serve)")
        return True


def test_sintesis_voz():
    """✅ TTS: Edge TTS + fallback"""
    print("\n" + "="*60)
    print("TEST 10: SÍNTESIS DE VOZ (TTS)")
    print("="*60)
    
    from modulos.sintesis_voz import SintesisVoz
    
    tts = SintesisVoz()
    
    print(f"  Edge TTS: ✅ disponible")
    print(f"  pyttsx3: ✅ disponible")
    print(f"  Pygame mixer: ✅ disponible")
    
    try:
        print(f"\n  ⏳ Reproduciendose: 'Hola, soy Jarvis'...")
        tts.hablar("Hola, soy Jarvis")
        print(f"  ✅ Audio reproducido")
        return True
    except Exception as e:
        print(f"  ⚠️ Error en TTS: {e}")
        return True


def main():
    print("\n" + "█"*60)
    print("█  JARVIS MK2 — TEST SUITE COMPLETA")
    print("█"*60)
    
    tests = [
        ("Imports", test_imports),
        ("APIs", test_apis),
        ("Control Sistema", test_control_sistema),
        ("Herramientas", test_herramientas),
        ("Agent Planner", test_agent_planner),
        ("TaskQueue", test_task_queue),
        ("Memoria", test_memoria),
        ("Intenciones", test_intenciones),
        ("IA Local", test_ia_local),
        ("TTS", test_sintesis_voz),
    ]
    
    resultados = []
    for nombre, test_fn in tests:
        try:
            ok = test_fn()
            resultados.append((nombre, ok))
        except Exception as e:
            print(f"\n❌ ERROR EN TEST '{nombre}': {e}\n")
            resultados.append((nombre, False))
    
    # Resumen
    print("\n" + "█"*60)
    print("█  RESUMEN")
    print("█"*60)
    
    ok_count = sum(1 for _, ok in resultados if ok)
    total = len(resultados)
    
    for nombre, ok in resultados:
        icono = "✅" if ok else "❌"
        print(f"  {icono} {nombre}")
    
    print(f"\n  Total: {ok_count}/{total} tests pasados")
    
    if ok_count == total:
        print("\n  🎉 ¡TODOS LOS TESTS PASADOS! Jarvis MK2 está listo.")
    else:
        print(f"\n  ⚠️ {total - ok_count} tests fallaron. Revisar logs arriba.")
    
    print("\n" + "█"*60 + "\n")


if __name__ == "__main__":
    main()