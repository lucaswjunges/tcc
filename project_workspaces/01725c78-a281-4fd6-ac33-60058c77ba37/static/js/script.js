// script.js

document.addEventListener('DOMContentLoaded', () => {
  const readingTypes = document.querySelectorAll('.reading-type');
  const paymentForm = document.getElementById('payment-form');
  const readingDescription = document.getElementById('reading-description');
  let selectedReading = null;

  readingTypes.forEach(type => {
    type.addEventListener('click', () => {
      readingTypes.forEach(t => t.classList.remove('selected'));
      type.classList.add('selected');
      selectedReading = type.dataset.reading;
      readingDescription.textContent = type.dataset.description;
      paymentForm.style.display = 'block';


      // Update price based on selected reading
      const priceElement = document.getElementById('price');
      priceElement.textContent = type.dataset.price;
      
      // Update hidden input field with selected reading ID for submission
      const readingIdInput = document.getElementById('reading-id');
      readingIdInput.value = selectedReading;



    });
  });

    // Handle form submission (Example - Replace with actual payment integration)
    paymentForm.addEventListener('submit', (event) => {
      event.preventDefault(); // Prevent default form submission

      // Perform payment processing here (e.g., Stripe, PayPal)
      // ...
  
      // After successful payment, redirect or display confirmation message
      alert("Payment successful! Your reading will be delivered soon.");

      // Or redirect to a thank you page:
      // window.location.href = "/thank-you";

      // Example: Send data to server using Fetch API
      // fetch('/process_payment', {
      //   method: 'POST',
      //   body: new FormData(paymentForm)
      // })
      // .then(response => response.json())
      // .then(data => {
      //   // Handle response from server
      //   console.log(data);
      // });


    });





});



// Function to display Tarot cards (replace with your actual card display logic)
function displayTarotCards(cards) {
  // ... Your logic to display the tarot cards ...
}


// Example: Fetch Tarot reading data from server (replace with your API endpoint)
// fetch('/api/tarot_reading')
//   .then(response => response.json())
//   .then(data => {
//     displayTarotCards(data.cards);
//   });