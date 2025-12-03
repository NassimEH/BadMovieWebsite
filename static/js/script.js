/* --- FONCTIONS D'ORIGINE --- */
function toggleVideo() {
  const trailer = document.querySelector('.trailer');
  const video = document.querySelector('video');
  video.pause();
  trailer.classList.toggle('active');
}

function changeBg(bg, title) {
  const banner = document.querySelector('.banner');
  const contents = document.querySelectorAll('.content');
  const categories = document.querySelector('.categories');
  
  banner.style.background = `url("/static/images/movies/${bg}")`;
  banner.style.backgroundSize = 'cover';
  banner.style.backgroundPosition = 'center';

  contents.forEach(content => {
    content.classList.remove('active');
    if (content.classList.contains(title)) content.classList.add('active');
  });

  if (categories) {
    categories.classList.remove('bg-little-mermaid', 'bg-65', 'bg-the-covenant', 'bg-the-black-demon', 'bg-the-tank');
    const bgClassMap = {
      'the-little-mermaid': 'bg-little-mermaid',
      'bg-65': 'bg-65',
      'the-covenant': 'bg-the-covenant',
      'the-black-demon': 'bg-the-black-demon',
      'the-tank': 'bg-the-tank'
    };
    if (bgClassMap[title]) categories.classList.add(bgClassMap[title]);
  }

  const moviesPage = document.querySelector('.movies-page');
  const moviesHero = document.querySelector('.movies-hero');
  if (moviesPage) {
     // (Même logique que précédemment...)
     moviesPage.classList.remove('bg-little-mermaid', 'bg-65', 'bg-the-covenant', 'bg-the-black-demon', 'bg-the-tank');
     // ... (simplifié pour la lisibilité, gardez votre code de mapping ici si besoin)
  }
  if (moviesHero) {
    moviesHero.style.background = `url("/static/images/movies/${bg}")`;
    moviesHero.style.backgroundSize = 'cover';
    moviesHero.style.backgroundPosition = 'center top';
  }
}

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

function buildMovieCardHtml(movie) {
  const imgSrc = movie.image ? movie.image : "/static/images/movies/the-little-mermaid.jpeg";
  const detailUrl = movie.id ? `/movies/${movie.id}` : "#";
  return `
    <a class="movie-card-link" href="${detailUrl}">
      <div class="movie-card">
        <div class="movie-card-poster"><img src="${imgSrc}" alt="${movie.title || "Affiche"}"></div>
        <div class="movie-card-info">
          <h3 class="movie-card-title">${movie.title || "Titre"}</h3>
          <p class="movie-card-meta">${movie.year || ""}${movie.duration ? ' • ' + movie.duration : ''}</p>
        </div>
      </div>
    </a>`;
}

function buildCategoryCarouselHtml(movies) {
  const cardsHtml = movies.map(buildMovieCardHtml).join('');
  return `
    <div class="category-carousel">
      <button class="category-carousel-btn prev" type="button"><i class="fa fa-chevron-left"></i></button>
      <div class="category-carousel-track">${cardsHtml}</div>
      <button class="category-carousel-btn next" type="button"><i class="fa fa-chevron-right"></i></button>
    </div>`;
}

function attachCategoryCarouselEvents() {
  const carousels = document.querySelectorAll('.category-carousel');
  carousels.forEach((carousel) => {
    const track = carousel.querySelector('.category-carousel-track');
    const prevBtn = carousel.querySelector('.category-carousel-btn.prev');
    const nextBtn = carousel.querySelector('.category-carousel-btn.next');
    if (!track) return;
    const getScrollAmount = () => {
      const firstCard = track.querySelector('.movie-card');
      if (!firstCard) return 0;
      const style = window.getComputedStyle(firstCard);
      return firstCard.offsetWidth + (parseInt(style.marginRight, 10) || 0);
    };
    if (prevBtn) prevBtn.addEventListener('click', () => track.scrollBy({ left: -getScrollAmount(), behavior: 'smooth' }));
    if (nextBtn) nextBtn.addEventListener('click', () => track.scrollBy({ left: getScrollAmount(), behavior: 'smooth' }));
  });
}

function loadMoviesByCategory() {
  const categorySections = document.querySelectorAll('.category');
  if (!categorySections.length) return;
  fetch('/movies/api/by-category')
    .then((r) => r.json())
    .then((data) => {
      if (data.error) return;
      categorySections.forEach((section) => {
        const h2 = section.querySelector('h2');
        const placeholder = section.querySelector('.category-content-placeholder');
        if (!h2 || !placeholder) return;
        const key = mapHeadingToCategoryKey(h2.textContent.trim());
        const movies = data[key] || [];
        placeholder.innerHTML = movies.length ? buildCategoryCarouselHtml(movies) : '<p class="no-movies">Aucun film.</p>';
      });
      attachCategoryCarouselEvents();
    })
    .catch((e) => console.error(e));
}
document.addEventListener('DOMContentLoaded', loadMoviesByCategory);


/* --- GESTION DES INTERACTIONS UTILISATEUR (AJOUT, VU, NOTE) --- */
document.addEventListener('DOMContentLoaded', function() {

    // --- Fonction utilitaire : Récupérer les données du film ---
    function getMovieDataFromPage() {
        const btn = document.querySelector('.js-watchlist-btn');
        if (!btn) return null;
        return {
            tmdb_id: btn.dataset.tmdbId,
            title: btn.dataset.title,
            image: btn.dataset.image,
            release_date: btn.dataset.releaseDate,
            runtime: btn.dataset.runtime,
            category: btn.dataset.category
        };
    }

    // --- 1. BOUTON "+ MA LISTE" ---
    document.body.addEventListener('click', function(e) {
        const btn = e.target.closest('.js-watchlist-btn');
        if (btn) {
            e.preventDefault();
            const movieData = {
                tmdb_id: btn.dataset.tmdbId,
                title: btn.dataset.title,
                image: btn.dataset.image,
                release_date: btn.dataset.releaseDate,
                runtime: btn.dataset.runtime,
                category: btn.dataset.category
            };
            fetch('/watchlist/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(movieData)
            })
            .then(r => r.status === 401 ? (window.location.href = "/auth/login") : r.json())
            .then(d => {
                if (d && d.success) {
                    btn.innerHTML = '<i class="fa fa-check"></i> Ajouté';
                    btn.style.opacity = '0.7';
                    btn.style.pointerEvents = 'none';
                } else {
                    alert("Erreur: " + (d.message || "Impossible d'ajouter"));
                }
            });
        }
    });

    // --- 2. BOUTON VU / NON VU ---
    const watchedBtn = document.getElementById('watched-btn');
    if (watchedBtn && !watchedBtn.disabled) {
        watchedBtn.addEventListener('click', function() {
            const isWatched = this.dataset.watched === 'true';
            const newState = !isWatched;
            const movieData = getMovieDataFromPage();
            if (!movieData) return;

            movieData.watched = newState;

            fetch('/watchlist/watched', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(movieData)
            })
            .then(r => r.json())
            .then(d => {
                if (d.success) {
                    this.dataset.watched = newState.toString();
                    if (newState) {
                        this.classList.add('watched');
                        this.querySelector('i').className = 'fa fa-check-circle';
                        this.querySelector('.watched-text').textContent = 'Vu';
                    } else {
                        this.classList.remove('watched');
                        this.querySelector('i').className = 'fa fa-eye';
                        this.querySelector('.watched-text').textContent = 'Marquer comme vu';
                    }
                }
            });
        });
    }

    // --- 3. SYSTEME D'ETOILES (Aspect V1 + Logique V2) ---
    const starRating = document.querySelector('.star-rating');
    const ratingValue = document.querySelector('.rating-value');
    const ratingLabel = document.querySelector('.rating-label');
    
    // Labels pour chaque note
    const ratingLabels = {
        0: '', 0.5: 'Horrible', 1: 'Très mauvais', 1.5: 'Mauvais', 2: 'Médiocre',
        2.5: 'Passable', 3: 'Correct', 3.5: 'Bon', 4: 'Très bon', 4.5: 'Excellent', 5: 'Chef d\'œuvre'
    };

    if (starRating && starRating.dataset.disabled !== 'true') {
        const starContainers = starRating.querySelectorAll('.star-container');
        const allStars = starRating.querySelectorAll('.star');
        let currentRating = parseFloat(starRating.dataset.currentScore) || 0; // Récupère le score depuis la BDD
        
        // Initialisation à l'affichage
        updateStarDisplay(starContainers, allStars, currentRating, false);
        if (ratingValue) ratingValue.textContent = currentRating;
        if (ratingLabel) ratingLabel.textContent = ratingLabels[currentRating] || '';

        // Fonction d'affichage visuel (Gère les classes active/hovered sur les spans)
        function updateStarDisplay(containers, stars, rating, isHover) {
            stars.forEach(s => s.classList.remove('active', 'hovered'));
            
            containers.forEach(container => {
                const cRating = parseFloat(container.dataset.rating);
                const starLeft = container.querySelector('.star-left');
                const starRight = container.querySelector('.star-right');

                // Logique pour colorier les demi-étoiles
                if (rating >= cRating) {
                    // Etoile pleine (les deux moitiés allumées)
                    starLeft.classList.add(isHover ? 'hovered' : 'active');
                    starRight.classList.add(isHover ? 'hovered' : 'active');
                } else if (rating >= cRating - 0.5) {
                    // Demi-étoile (seulement la moitié gauche)
                    starLeft.classList.add(isHover ? 'hovered' : 'active');
                }
            });
        }

        // Gestion du survol
        allStars.forEach(star => {
            star.addEventListener('mouseenter', function() {
                const hoverRating = parseFloat(this.dataset.rating);
                updateStarDisplay(starContainers, allStars, hoverRating, true);
                if (ratingLabel) ratingLabel.textContent = ratingLabels[hoverRating] || '';
            });
        });

        starRating.addEventListener('mouseleave', function() {
            updateStarDisplay(starContainers, allStars, currentRating, false);
            if (ratingLabel) ratingLabel.textContent = ratingLabels[currentRating] || '';
        });

        // Gestion du clic (Envoi BDD)
        allStars.forEach(star => {
            star.addEventListener('click', function() {
                const newRating = parseFloat(this.dataset.rating);
                const movieData = getMovieDataFromPage();
                
                if (!movieData) return;

                movieData.score = newRating;

                fetch('/watchlist/rate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(movieData)
                })
                .then(r => r.status === 401 ? (window.location.href = "/auth/login") : r.json())
                .then(d => {
                    if (d.success) {
                        currentRating = newRating;
                        updateStarDisplay(starContainers, allStars, currentRating, false);
                        if (ratingValue) ratingValue.textContent = currentRating;
                        
                        // Marquer comme vu automatiquement si noté
                        if (watchedBtn) {
                            watchedBtn.classList.add('watched');
                            watchedBtn.dataset.watched = "true";
                            watchedBtn.querySelector('i').className = 'fa fa-check-circle';
                            watchedBtn.querySelector('.watched-text').textContent = 'Vu';
                        }
                    }
                });
            });
        });
    }
});