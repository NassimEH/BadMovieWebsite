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

// --- Chargement des films par catégorie via l'API ---

/**
 * Convertit le titre affiché dans la section (ex: "Films d'action")
 * en nom de catégorie tel qu'enregistré en base (ex: "Action").
 */
function mapHeadingToCategoryKey(heading) {
  if (!heading) return 'Autre';

  const text = heading.toLowerCase();

  if (text.includes("action")) return "Action";
  if (text.includes("horreur")) return "Horreur";
  if (text.includes("fantastique")) return "Fantastique";
  if (text.includes("science-fiction") || text.includes("science fiction")) return "Science-Fiction";
  if (text.includes("drame")) return "Drame";
  if (text.includes("comédie") || text.includes("comedie")) return "Comédie";
  if (text.includes("thriller")) return "Thriller";
  if (text.includes("guerre")) return "Guerre";
  if (text.includes("romance")) return "Romance";
  if (text.includes("animation")) return "Animation";
  if (text.includes("documentaire")) return "Documentaire";

  return "Autre";
}

/**
 * Construit le HTML d'une carte de film dans une section de catégorie.
 */
function buildMovieCardHtml(movie) {
  const imgSrc = movie.image
    ? movie.image                                  // URL complète TMDB ou autre
    : "/static/images/movies/the-little-mermaid.jpeg"; // image par défaut

  const yearText = movie.year ? movie.year : "";
  const durationText = movie.duration ? ` • ${movie.duration}` : "";

  return `
    <div class="movie-card">
      <div class="movie-card-poster">
        <img src="${imgSrc}" alt="${movie.title || "Affiche film"}">
      </div>
      <div class="movie-card-info">
        <h3 class="movie-card-title">${movie.title || "Titre indisponible"}</h3>
        <p class="movie-card-meta">
          ${yearText}${durationText}
        </p>
      </div>
    </div>
  `;
}

/**
 * Construit le HTML d'un carousel pour une catégorie donnée.
 */
function buildCategoryCarouselHtml(movies) {
  const cardsHtml = movies.map(buildMovieCardHtml).join('');

  return `
    <div class="category-carousel">
      <button class="category-carousel-btn prev" type="button" aria-label="Précédent">
        <i class="fa fa-chevron-left" aria-hidden="true"></i>
      </button>
      <div class="category-carousel-track">
        ${cardsHtml}
      </div>
      <button class="category-carousel-btn next" type="button" aria-label="Suivant">
        <i class="fa fa-chevron-right" aria-hidden="true"></i>
      </button>
    </div>
  `;
}

/**
 * Initialise les événements de navigation pour tous les carousels de catégories.
 */
function attachCategoryCarouselEvents() {
  const carousels = document.querySelectorAll('.category-carousel');
  if (!carousels.length) return;

  carousels.forEach((carousel) => {
    const track = carousel.querySelector('.category-carousel-track');
    const prevBtn = carousel.querySelector('.category-carousel-btn.prev');
    const nextBtn = carousel.querySelector('.category-carousel-btn.next');

    if (!track) return;

    const getScrollAmount = () => {
      const firstCard = track.querySelector('.movie-card');
      if (!firstCard) return 0;

      const style = window.getComputedStyle(firstCard);
      const marginRight = parseInt(style.marginRight, 10) || 0;
      return firstCard.offsetWidth + marginRight;
    };

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        const amount = getScrollAmount();
        if (!amount) return;
        track.scrollBy({
          left: -amount,
          behavior: 'smooth',
        });
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        const amount = getScrollAmount();
        if (!amount) return;
        track.scrollBy({
          left: amount,
          behavior: 'smooth',
        });
      });
    }
  });
}

/**
 * Charge les films depuis l'API et remplit toutes les sections .category
 * présentes sur la page (index et movies_list).
 */
function loadMoviesByCategory() {
  const categorySections = document.querySelectorAll('.category');
  if (!categorySections.length) return;

  fetch('/movies/api/by-category')
    .then((response) => {
      if (!response.ok) {
        throw new Error("Erreur lors du chargement des films");
      }
      return response.json();
    })
    .then((data) => {
      categorySections.forEach((section) => {
        const headingEl = section.querySelector('h2');
        const placeholder = section.querySelector('.category-content-placeholder');

        if (!headingEl || !placeholder) return;

        const categoryKey = mapHeadingToCategoryKey(headingEl.textContent.trim());
        const movies = data[categoryKey] || [];

        if (!movies.length) {
          placeholder.innerHTML = '<p class="no-movies">Aucun film pour cette catégorie pour le moment.</p>';
          return;
        }

        // Injecter un carousel pour la catégorie
        placeholder.innerHTML = buildCategoryCarouselHtml(movies);
      });

      // Une fois tous les contenus injectés, initialiser les carousels
      attachCategoryCarouselEvents();
    })
    .catch((error) => {
      console.error(error);
    });
}

// Lancer automatiquement le chargement des films par catégorie
document.addEventListener('DOMContentLoaded', loadMoviesByCategory);
