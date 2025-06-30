document.addEventListener('DOMContentLoaded', function() {
    // Array de cartas do Tarô (Arcanos Maiores e Menores)
    const tarotCards = [
        {
            id: "00",
            name: "00 - O Iluminado",
            upright: "Você está no caminho correto, seguindo sua intuição e visão. A iluminação está ao seu alcance.",
            reversed: "Você pode estar perdido ou confuso. Busque clareza e confie em seu guia interno."
        },
        {
            id: "01",
            name: "01 - O Mago",
            upright: "Você tem poderes mágicos e habilidades naturais. Use sua inteligência e criatividade.",
            reversed: "Você pode estar desperdiçando seu potencial ou duvidando de suas habilidades."
        },
        {
            id: "02",
            name: "02 - A Fada",
            upright: "Curadores e protetores aparecerão em sua vida. Prepare-se para receber ajuda.",
            reversed: "Você pode estar bloqueado em seu caminho curativo ou perdendo sua magia."
        },
        {
            id: "03",
            name: "03 - O Guerrero",
            upright: "Você é forte e está pronto para a batalha. Aja com coragem e determinação.",
            reversed: "Você pode estar evitando confrontos ou desafiando sua própria força."
        },
        {
            id: "04",
            name: "04 - A Dama de Copas",
            upright: "Você é uma mulher generosa e compassiva. Seu coração está aberto ao amor.",
            reversed: "Você pode estar sendo excessivamente sentimental ou tendo dificuldades emocionais."
        },
        {
            id: "05",
            name: "05 - O Guerrero de Copas",
            upright: "Você defende seus valores e sentimentos. Aja com coragem emocional.",
            reversed: "Você pode estar tendo dificuldades para expressar seus sentimentos ou defendendo excessivamente."
        },
        {
            id: "06",
            name: "06 - A Dama de Espadas",
            upright: "Você é uma mulher decidida e corajosa. Proteja seus pensamentos e ideias.",
            reversed: "Você pode estar tendo dificuldades para tomar decisões ou agindo de forma impulsiva."
        },
        {
            id: "07",
            name: "07 - O Guerrero de Espadas",
            upright: "Você está pronto para a luta mental. Use sua mente afiada para resolver problemas.",
            reversed: "Você pode estar envolvido em conflitos desnecessários ou tendo dificuldades para pensar claramente."
        },
        {
            id: "08",
            name: "08 - A Dama de Ouros",
            upright: "Você é uma mulher criativa e produtiva. Celebre seu lado prático e material.",
            reversed: "Você pode estar negligenciando seu lado criativo ou tendo problemas financeiros."
        },
        {
            id: "09",
            name: "09 - O Guerrero de Ouros",
            upright: "Você está pronto para ação e conquista. Use sua energia para criar algo novo.",
            reversed: "Você pode estar procrastinando ou tendo dificuldades para iniciar projetos."
        },
        {
            id: "10",
            name: "10 - A Roda da Fortuna",
            upright: "Sua vida está mudando em direção a uma nova fase. Aprenda a navegar essas mudanças.",
            reversed: "Você pode estar resistindo às mudanças ou enfrentando adversidades significativas."
        },
        {
            id: "11",
            name: "11 - Justiça",
            upright: "A verdade prevalecerá. Confie nos resultados justos e equilibrados.",
            reversed: "Você pode estar tentando enganar alguém ou enfrentando uma situação desequilibrada."
        },
        {
            id: "12",
            name: "12 - A Hiena",
            upright: "Você está pronto para descobrir a verdade oculta. Não se deixe enganar.",
            reversed: "Você pode estar sendo enganado ou tendo dificuldades para ver além da aparência."
        },
        {
            id: "13",
            name: "13 - O Mundo",
            upright: "Você está conectado a todo o universo. Esta é uma posição de realização e sucesso.",
            reversed: "Você pode estar desconectado do todo ou tendo dificuldades para encontrar propósito."
        },
        {
            id: "14",
            name: "14 - A Forja",
            upright: "Você está passando por uma transformação necessária. Aja com paciência e persistência.",
            reversed: "Você pode estar se forçando demais ou tendo dificuldades para mudar."
        },
        {
            id: "15",
            name: "15 - A Justiça Reversa",
            upright: "A injustiça pode estar sendo corrigida. Busque a verdade e a equidade.",
            reversed: "Você pode estar envolvido em uma situação desequilibrada ou tendo dificuldades para encontrar justiça."
        },
        {
            id: "16",
            name: "16 - A Temperança",
            upright: "Você precisa equilibrar forças opostas. Aja com moderação e paciência.",
            reversed: "Você pode estar tendo dificuldades para equilibrar diferentes aspectos da sua vida."
        },
        {
            id: "17",
            name: "17 - A Força",
            upright: "Você tem poder interior para superar obstáculos. Aja com determinação e coragem.",
            reversed: "Você pode estar enfrentando resistência ou tendo dificuldades para impor sua vontade."
        },
        {
            id: "18",
            name: "18 - O Herói",
            upright: "Você está pronto para liderar e proteger. Aja com coragem e nobreza.",
            reversed: "Você pode estar tendo dificuldades para assumir a liderança ou proteger seus valores."
        },
        {
            id: "19",
            name: "19 - A Rua",
            upright: "Você está no caminho certo. Continue seguindo sua intuição e propósito.",
            reversed: "Você pode estar perdido ou tendo dificuldades para encontrar seu caminho."
        },
        {
            id: "20",
            name: "20 - A Lua",
            upright: "Sonhos, medos e ilusões estão presentes. Busque clareza e confie em seu guia interno.",
            reversed: "Você pode estar tendo visões distorcidas ou tendo dificuldades para distinguir a realidade."
        },
        {
            id: "21",
            name: "21 - O Juiz",
            upright: "Você precisa tomar uma decisão importante. Considere todos os aspectos antes de decidir.",
            reversed: "Você pode estar procrastinando decisões importantes ou tendo dificuldades para avaliar opções."
        },
        {
            id: "22",
            name: "22 - A Torre",
            upright: "Mudanças drásticas estão por vir. Aceite a necessidade de transformação.",
            reversed: "Você pode estar tentando evitar mudanças ou tendo dificuldades para destruir o velho para fazer lugar ao novo."
        }
    ];

    // Elementos DOM
    const questionInput = document.getElementById('question');
    const drawButton = document.getElementById('draw-button');
    const resultDiv = document.getElementById('result');
    const shuffleButton = document.getElementById('shuffle-button');
    const resetButton = document.getElementById('reset-button');
    const packageSelect = document.getElementById('package-select');
    const buyButton = document.getElementById('buy-button');
    const balanceDiv = document.getElementById('balance');

    // Variáveis de estado
    let userBalance = 5.00; // Saldo inicial do usuário
    let cardsDrawn = [];
    let packagePurchased = false;

    // Função para embaralhar as cartas
    function shuffleCards() {
        const shuffled = [...tarotCards];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }

    // Função para realizar uma tiragem
    function drawCards() {
        const question = questionInput.value.trim();
        if (!question) {
            alert('Por favor, digite uma pergunta antes de fazer a tiragem.');
            return;
        }

        // Verificar se o usuário tem saldo suficiente
        const packageCost = packagePurchased ? 0 : 3.00;
        if (userBalance < packageCost) {
            alert('Saldo insuficiente. Compre um pacote de tiragens ou compre uma tiragem única por 3,00.');
            return;
        }

        // Atualizar o saldo
        userBalance -= packageCost;
        updateBalance();

        // Embaralhar as cartas
        const shuffledCards = shuffleCards();
        cardsDrawn = [];

        // Determinar quantas cartas tirar baseado no pacote
        let numberOfDraws = 3;
        if (packagePurchased) {
            numberOfDraws = 5;
        }

        // Tirar as cartas
        for (let i = 0; i < numberOfDraws; i++) {
            const card = shuffledCards[i];
            cardsDrawn.push({
                card: card,
                upright: Math.random() > 0.5 ? card.upright : card.reversed
            });
        }

        // Exibir os resultados
        displayResults();

        // Limpar o campo de pergunta
        questionInput.value = '';
    }

    // Função para exibir os resultados
    function displayResults() {
        resultDiv.innerHTML = '<h2>Resultado da Tiragem</h2>';
        
        cardsDrawn.forEach((draw, index) => {
            const cardDiv = document.createElement('div');
            cardDiv.className = 'card-result';
            
            cardDiv.innerHTML = `
                <div class="card-number">${index + 1}. ${draw.card.name}</div>
                <div class="card-orientation">${draw.upright.includes('Você') ? 'Posição Direita' : 'Posição Invertida'}</div>
                <div class="card-meaning">${draw.upright}</div>
            `;
            
            resultDiv.appendChild(cardDiv);
        });
    }

    // Função para atualizar o saldo do usuário
    function updateBalance() {
        balanceDiv.textContent = userBalance.toFixed(2);
    }

    // Função para comprar um pacote
    function buyPackage() {
        const packagePrice = 15.00;
        if (userBalance < packagePrice) {
            alert('Saldo insuficiente para comprar o pacote.');
            return;
        }

        userBalance -= packagePrice;
        packagePurchased = true;
        updateBalance();
        alert('Pacote adquirido com sucesso! Você tem direito a 5 tiragens por sessão.');
    }

    // Função para reiniciar a tiragem
    function resetDraw() {
        cardsDrawn = [];
        resultDiv.innerHTML = '<h2>Resultado da Tiragem</h2>';
    }

    // Event listeners
    drawButton.addEventListener('click', drawCards);
    shuffleButton.addEventListener('click', () => {
        if (cardsDrawn.length > 0) {
            // Embaralhar apenas as cartas não sorteadas
            const remainingCards = tarotCards.filter(card => 
                !cardsDrawn.some(draw => draw.card.id === card.id)
            );
            
            const shuffledRemaining = shuffleCards(remainingCards);
            
            // Atualizar as cartas não sorteadas
            tarotCards.forEach(card => {
                const draw = cardsDrawn.find(d => d.card.id === card.id);
                if (!draw) {
                    const newDraw = shuffledRemaining.find(c => c.id === card.id);
                    if (newDraw) {
                        cardsDrawn.push({
                            card: newDraw,
                            upright: Math.random() > 0.5 ? newDraw.upright : newDraw.reversed
                        });
                    }
                }
            });
            
            displayResults();
        }
    });
    resetButton.addEventListener('click', resetDraw);
    buyButton.addEventListener('click', buyPackage);

    // Inicializar o saldo
    updateBalance();
});