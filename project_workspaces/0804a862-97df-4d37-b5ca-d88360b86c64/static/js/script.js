// script.js

document.addEventListener('DOMContentLoaded', () => {
  const cardContainers = document.querySelectorAll('.card-container');

  cardContainers.forEach(container => {
    container.addEventListener('click', () => {
      // Lógica para lidar com o clique em uma carta.
      // Exemplo: exibir a descrição da carta, 
      // redirecionar para uma página de detalhes, etc.

      const cardId = container.dataset.cardId;
      console.log(`Carta clicada: ${cardId}`);

      // Exemplo de requisição AJAX para buscar informações da carta
      fetch(`/card_details/${cardId}`)
        .then(response => response.json())
        .then(data => {
          // Exibir os detalhes da carta em um modal, por exemplo
          const modal = document.getElementById('cardModal');
          modal.querySelector('.modal-title').textContent = data.name;
          modal.querySelector('.modal-body').textContent = data.description;
          $(modal).modal('show'); // Assumindo que você está usando Bootstrap para o modal

        }).catch(error => {
          console.error("Erro ao buscar detalhes da carta:", error);
          alert("Erro ao buscar detalhes da carta. Por favor, tente novamente.");
        });



    });
  });


  // Event listener para o formulário de contato (se houver)
  const contactForm = document.getElementById('contactForm');
  if (contactForm) {
    contactForm.addEventListener('submit', (event) => {
      event.preventDefault(); // Impede o envio padrão do formulário

      // Lógica para enviar os dados do formulário via AJAX
      // ...

      alert('Mensagem enviada com sucesso!');
      contactForm.reset(); // Limpa o formulário após o envio
    });
  }


  // Outras funcionalidades JavaScript, como animações, etc.
  // Exemplo: animação suave para rolagem até uma seção específica
  const navbarLinks = document.querySelectorAll('nav a[href^="#"]');
  navbarLinks.forEach(link => {
    link.addEventListener('click', function(event) {
      event.preventDefault();
      const targetId = this.getAttribute('href');
      const targetElement = document.querySelector(targetId);

      window.scrollTo({
        top: targetElement.offsetTop,
        behavior: 'smooth' // Rolagem suave
      });
    });
  });


});


// Função auxiliar para exibir uma mensagem de erro (opcional)
function showErrorMessage(message) {
  // Implemente a lógica para exibir a mensagem de erro na página
  console.error(message);
}