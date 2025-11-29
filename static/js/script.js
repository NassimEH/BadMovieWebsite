function toggleVideo() {
  const trailer = document.querySelector('.trailer');
  const video = document.querySelector('video');
  video.pause();
  trailer.classList.toggle('active');
}
// change the background images and movie content text
function changeBg(bg, title) {
  const banner = document.querySelector('.banner');
  const contents = document.querySelectorAll('.content');
  const categories = document.querySelector('.categories');
  
  // Utilisation du chemin Flask static
  banner.style.background = `url("/static/images/movies/${bg}")`;
  banner.style.backgroundSize = 'cover';
  banner.style.backgroundPosition = 'center';

  contents.forEach(content => {
    content.classList.remove('active');
    if (content.classList.contains(title)) {
      content.classList.add('active');
    }
  });

  // Mettre à jour l'image de fond floue de la section categories et de la page movies
  if (categories) {
    // Retirer toutes les classes de fond existantes
    categories.classList.remove('bg-little-mermaid', 'bg-65', 'bg-the-covenant', 'bg-the-black-demon', 'bg-the-tank');
    
    // Ajouter la classe correspondante au film sélectionné
    // Mapper les noms de films aux classes CSS
    const bgClassMap = {
      'the-little-mermaid': 'bg-little-mermaid',
      'bg-65': 'bg-65',
      'the-covenant': 'bg-the-covenant',
      'the-black-demon': 'bg-the-black-demon',
      'the-tank': 'bg-the-tank'
    };
    
    if (bgClassMap[title]) {
      categories.classList.add(bgClassMap[title]);
    }
  }

  // Mettre à jour le fond de la page movies si elle existe
  const moviesPage = document.querySelector('.movies-page');
  const moviesHero = document.querySelector('.movies-hero');
  
  if (moviesPage) {
    // Retirer toutes les classes de fond existantes
    moviesPage.classList.remove('bg-little-mermaid', 'bg-65', 'bg-the-covenant', 'bg-the-black-demon', 'bg-the-tank');
    
    // Mapper les noms de films aux classes CSS
    const bgClassMap = {
      'the-little-mermaid': 'bg-little-mermaid',
      'bg-65': 'bg-65',
      'the-covenant': 'bg-the-covenant',
      'the-black-demon': 'bg-the-black-demon',
      'the-tank': 'bg-the-tank'
    };
    
    if (bgClassMap[title]) {
      moviesPage.classList.add(bgClassMap[title]);
    }
  }

  // Mettre à jour le fond du hero directement
  if (moviesHero) {
    moviesHero.style.background = `url("/static/images/movies/${bg}")`;
    moviesHero.style.backgroundSize = 'cover';
    moviesHero.style.backgroundPosition = 'center top';
  }
}
