from flask import Blueprint, request, jsonify, render_template
import random
import os
from datetime import datetime

tirar_carta_bp = Blueprint('tirar_carta', __name__)

# Estrutura de dados para as cartas do tarot
tarot_deck = [
    {
        "id": 1,
        "name": "The Fool",
        "image": "static/images/tarot/001_The_Fool.jpg",
        "upright": "The Fool represents new beginnings, innocence, and spontaneity. It encourages you to take a leap of faith and trust in the universe.",
        "reversed": "Reversed The Fool suggests hesitation, recklessness, or a need to be more cautious. It may indicate that you're ignoring your intuition or taking unnecessary risks."
    },
    {
        "id": 2,
        "name": "The Magician",
        "image": "static/images/tarot/002_The_Magician.jpg",
        "upright": "The Magician represents resourcefulness, action, and manifestation. It indicates that you have the tools to make your desires a reality.",
        "reversed": "Reversed The Magician suggests untapped potential, manipulation, or a lack of focus. It may indicate that you're not using your skills effectively or that someone else is manipulating circumstances."
    },
    {
        "id": 3,
        "name": "The High Priestess",
        "image": "static/images/tarot/003_The_High_Priestess.jpg",
        "upright": "The High Priestess represents intuition, unconscious knowledge, and the divine feminine. It suggests trusting your inner voice and intuition.",
        "reversed": "Reversed The High Priestess indicates disconnected intuition, denial, or ignoring your inner wisdom. It may suggest that you're not listening to your intuition or are out of touch with your emotions."
    },
    {
        "id": 4,
        "name": "The Empress",
        "image": "static/images/tarot/004_The_Empress.jpg",
        "upright": "The Empress represents abundance, beauty, motherhood, and nature. It indicates a time of growth, nurturing, and receiving.",
        "reversed": "Reversed The Empress suggests barrenness, oppression, or an imbalance in nurturing relationships. It may indicate that you're not receiving what you need or that you're being overly controlling."
    },
    {
        "id": 5,
        "name": "The Emperor",
        "image": "static/images/tarot/005_The_Emperor.jpg",
        "upright": "The Emperor represents structure, authority, and stability. It indicates a need for order, control, and establishing boundaries.",
        "reversed": "Reversed The Emperor suggests rigidity, excessive control, or an outdated authority structure. It may indicate that you're being too controlling or that authority figures are being stubborn."
    },
    {
        "id": 6,
        "name": "The Hierophant",
        "image": "static/images/tarot/006_The_Hierophant.jpg",
        "upright": "The Hierophant represents tradition, spirituality, and conformity. It indicates a need for guidance, mentorship, or established values.",
        "reversed": "Reversed The Hierophant suggests rebellion against authority, outdated traditions, or a need to question established beliefs. It may indicate that you're resisting conventional wisdom."
    },
    {
        "id": 7,
        "name": "The Lovers",
        "image": "static/images/tarot/007_The_Lovers.jpg",
        "upright": "The Lovers represents harmony, relationships, and choices. It indicates a need for alignment between values, beliefs, and actions.",
        "reversed": "Reversed The Lovers suggests imbalance in relationships, poor choices, or a lack of harmony between values and actions. It may indicate a mismatch in a relationship or a wrong decision."
    },
    {
        "id": 8,
        "name": "The Chariot",
        "image": "static/images/tarot/008_The_Chariot.jpg",
        "upright": "The Chariot represents willpower, control, and victory. It indicates that you have the power to overcome obstacles and achieve your goals.",
        "reversed": "Reversed The Chariot suggests lack of willpower, being controlled by others, or feeling stuck. It may indicate that you're not in control of your situation or that you're being pulled in different directions."
    },
    {
        "id": 9,
        "name": "Strength",
        "image": "static/images/tarot/009_Strength.jpg",
        "upright": "Strength represents courage, persuasion, and inner power. It indicates that you have the strength to overcome challenges and influence others.",
        "reversed": "Reversed Strength suggests lack of courage, weakness, or a need to find inner strength. It may indicate that you're feeling vulnerable or that you're not standing up for yourself."
    },
    {
        "id": 10,
        "name": "The Hermit",
        "image": "static/images/tarot/010_The_Hermit.jpg",
        "upright": "The Hermit represents introspection, guidance, and inner wisdom. It indicates a need for solitude, reflection, and seeking inner knowledge.",
        "reversed": "Reversed The Hermit suggests isolation, withdrawal, or a lack of introspection. It may indicate that you're avoiding your inner wisdom or that you're not seeking guidance."
    },
    {
        "id": 11,
        "name": "Wheel of Fortune",
        "image": "static/images/tarot/011_Wheel_of_Fortune.jpg",
        "upright": "The Wheel of Fortune represents destiny, karma, and cycles. It indicates that the universe is in motion and that your life is following a path.",
        "reversed": "Reversed Wheel of Fortune suggests bad luck, resistance to change, or feeling stuck in a cycle. It may indicate that you're fighting against the natural flow of life."
    },
    {
        "id": 12,
        "name": "Justice",
        "image": "static/images/tarot/012_Justice.jpg",
        "upright": "Justice represents law, truth, and consequences. It indicates that actions have consequences and that fairness and balance are important.",
        "reversed": "Reversed Justice suggests dishonesty, unfairness, or a need to reconsider a decision. It may indicate that you're being punished for past actions or that you're being treated unfairly."
    },
    {
        "id": 13,
        "name": "The Hanged Man",
        "image": "static/images/tarot/013_The_Hanged_Man.jpg",
        "upright": "The Hanged Man represents sacrifice, surrender, and new perspectives. It indicates that letting go of something can lead to greater understanding.",
        "reversed": "Reversed The Hanged Man suggests stubbornness, resistance to change, or holding onto the past. It may indicate that you're refusing to see a different perspective."
    },
    {
        "id": 14,
        "name": "Death",
        "image": "static/images/tarot/014_Death.jpg",
        "upright": "Death represents endings, transitions, and change. It indicates that an old phase is ending and making way for new beginnings.",
        "reversed": "Reversed Death suggests resistance to change, fear of endings, or a need to let go of something. It may indicate that you're afraid of change or that you're holding onto something that should be released."
    },
    {
        "id": 15,
        "name": "Temperance",
        "image": "static/images/tarot/015_Temperance.jpg",
        "upright": "Temperance represents moderation, balance, and patience. It indicates that finding balance and exercising self-control will lead to success.",
        "reversed": "Reversed Temperance suggests excess, imbalance, or impatience. It may indicate that you're giving up too soon or that you're not finding balance in your life."
    },
    {
        "id": 16,
        "name": "The Devil",
        "image": "static/images/tarot/016_The_Devil.jpg",
        "upright": "The Devil represents bondage, addiction, and illusion. It indicates that you may be trapped by your own desires or that you need to break free from negative patterns.",
        "reversed": "Reversed The Devil suggests freedom from addiction, illusion, or negative patterns. It may indicate that you're breaking free from a limiting belief or situation."
    },
    {
        "id": 17,
        "name": "The Tower",
        "image": "static/images/tarot/017_The_Tower.jpg",
        "upright": "The Tower represents sudden change, upheaval, and revelation. It indicates that a dramatic event may be necessary to bring about growth and understanding.",
        "reversed": "Reversed The Tower suggests avoiding a crisis, delaying an inevitable change, or preventing a revelation. It may indicate that you're trying to avoid a necessary change."
    },
    {
        "id": 18,
        "name": "The Star",
        "image": "static/images/tarot/018_The_Star.jpg",
        "upright": "The Star represents hope, faith, and renewal. It indicates that there is a possibility for healing and that faith in the universe will be rewarded.",
        "reversed": "Reversed The Star suggests despair, lack of faith, or a need to rekindle hope. It may indicate that you're losing faith or that you're not believing in a better outcome."
    },
    {
        "id": 19,
        "name": "The Moon",
        "image": "static/images/tarot/019_The_Moon.jpg",
        "upright": "The Moon represents illusion, anxiety, and the subconscious. It indicates that you may be experiencing fears or that you need to address hidden issues.",
        "reversed": "Reversed The Moon suggests dispelling illusions, overcoming fears, or achieving clarity. It may indicate that you're facing your fears or that illusions are being revealed."
    },
    {
        "id": 20,
        "name": "The Sun",
        "image": "static/images/tarot/020_The_Sun.jpg",
        "upright": "The Sun represents success, vitality, and positivity. It indicates that good things are on the horizon and that your efforts will be rewarded.",
        "reversed": "Reversed The Sun suggests temporary depression, ego problems, or a delay in success. It may indicate that you're feeling down or that something that seemed successful is now faltering."
    },
    {
        "id": 21,
        "name": "Judgment",
        "image": "static/images/tarot/021_Judgment.jpg",
        "upright": "Judgment represents awakening, reckoning, and second chances. It indicates that it's time to face your past, make amends, and start anew.",
        "reversed": "Reversed Judgment suggests avoidance of reckoning, denial, or not accepting a second chance. It may indicate that you're avoiding facing your past or that you're not accepting a necessary change."
    },
    {
        "id": 22,
        "name": "The World",
        "image": "static/images/tarot/022_The_World.jpg",
        "upright": "The World represents completion, achievement, and wholeness. It indicates that a cycle is complete and that you have achieved your goals.",
        "reversed": "Reversed The World suggests feeling unfulfilled, incomplete, or not having reached your goals. It may indicate that you're not accepting completion or that something is missing."
    }
]

@tirar_carta_bp.route('/tirar_carta', methods=['GET', 'POST'])
def tirar_carta():
    if request.method == 'POST':
        # Lógica para processar o pagamento e tirar a carta
        # Aqui você integraria um gateway de pagamento
        # Para este exemplo, vamos simular o processo
        
        # Verificar se o usuário está logado (em um sistema real, você precisaria verificar isso)
        # user_id = request.form.get('user_id')
        
        # Processar pagamento (simulado)
        payment_processed = True  # Em um sistema real, isso seria processado via API de pagamento
        
        if payment_processed:
            # Tirar uma carta aleatória
            carta = random.choice(tarot_deck)
            
            # Registrar a leitura no banco de dados (simulado)
            leitura = {
                "user_id": "user123",  # Em um sistema real, seria o ID do usuário logado
                "carta_id": carta["id"],
                "data": datetime.now().isoformat(),
                "interpretacao": carta["upright"]
            }
            
            # Em um sistema real, você salvaria no banco de dados
            # save_to_database(leitura)
            
            return jsonify({
                "success": True,
                "carta": {
                    "id": carta["id"],
                    "name": carta["name"],
                    "image": carta["image"],
                    "interpretacao": carta["upright"]
                }
            })
        else:
            return jsonify({"success": False, "message": "Falha ao processar pagamento"})
    
    # Método GET - Mostrar página para tirar carta
    return render_template('tirar_carta.html')

@tirar_carta_bp.route('/carta/<int:carta_id>')
def mostrar_carta(carta_id):
    # Em um sistema real, você buscaria no banco de dados qual carta o usuário tirou
    # Para este exemplo, vamos buscar pela ID
    carta = next((c for c in tarot_deck if c["id"] == carta_id), None)
    
    if carta:
        return render_template('carta.html', carta=carta)
    else:
        return jsonify({"error": "Carta não encontrada"}, 404)

@tirar_carta_bp.route('/historico')
def historico_leituras():
    # Em um sistema real, você buscaria no banco de dados o histórico do usuário
    # Para este exemplo, vamos simular um histórico
    historico = [
        {"id": 1, "carta_id": 1, "data": "2023-10-01T10:30:00", "interpretacao": "The Fool represents new beginnings..."},
        {"id": 2, "carta_id": 21, "data": "2023-10-02T14:15:00", "interpretacao": "Judgment represents awakening..."}
    ]
    
    return jsonify(historico)

@tirar_carta_bp.route('/precos')
def precos():
    return jsonify({
        "simples": 29.99,
        "detalhada": 49.99,
        "premium": 79.99
    })