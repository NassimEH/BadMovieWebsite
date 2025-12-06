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
  const movieId = movie.id || movie.tmdb_id || '';
  const movieTitle = movie.title || "Titre";
  const movieImage = movie.image || imgSrc;
  const movieYear = movie.year || '';
  const movieCategory = movie.category || 'Autre';
  
  return `
    <div class="movie-card-wrapper">
      <a class="movie-card-link" href="${detailUrl}">
        <div class="movie-card">
          <div class="movie-card-poster">
            <img src="${imgSrc}" alt="${movieTitle}">
            <button class="movie-card-add-btn js-watchlist-btn" 
                    data-tmdb-id="${movieId}"
                    data-title="${movieTitle}"
                    data-image="${movieImage}"
                    data-release-date="${movieYear ? movieYear + '-01-01' : ''}"
                    data-runtime="${movie.duration || ''}"
                    data-category="${movieCategory}"
                    aria-label="Ajouter ${movieTitle} à ma liste"
                    title="Ajouter à ma liste">
              <i class="fa fa-plus" aria-hidden="true"></i>
            </button>
          </div>
          <div class="movie-card-info">
            <h3 class="movie-card-title">${movieTitle}</h3>
            <p class="movie-card-meta">${movieYear || ""}${movie.duration ? ' • ' + movie.duration : ''}</p>
          </div>
        </div>
      </a>
    </div>`;
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
  
  // Afficher un indicateur de chargement
  categorySections.forEach((section) => {
    const placeholder = section.querySelector('.category-content-placeholder');
    if (placeholder) {
      placeholder.innerHTML = '<div class="loading-spinner"><i class="fa fa-spinner fa-spin"></i> Chargement...</div>';
    }
  });
  
  fetch('/movies/api/by-category')
    .then((r) => {
      if (!r.ok) throw new Error('Erreur réseau');
      return r.json();
    })
    .then((data) => {
      if (data.error) {
        console.error('Erreur API:', data.error);
        categorySections.forEach((section) => {
          const placeholder = section.querySelector('.category-content-placeholder');
          if (placeholder) {
            placeholder.innerHTML = '<p class="no-movies">Erreur de chargement.</p>';
          }
        });
        return;
      }
      
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
    .catch((e) => {
      console.error('Erreur lors du chargement des films:', e);
      categorySections.forEach((section) => {
        const placeholder = section.querySelector('.category-content-placeholder');
        if (placeholder) {
          placeholder.innerHTML = '<p class="no-movies">Erreur de chargement.</p>';
        }
      });
    });
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

    // --- 1. BOUTON "+ MA LISTE" / "DANS MA LISTE" ---
    document.body.addEventListener('click', function(e) {
        const btn = e.target.closest('.js-watchlist-btn');
        if (btn) {
            e.preventDefault();
            e.stopPropagation(); // Empêcher la navigation vers la page du film si c'est un bouton sur carte
            
            const movieData = {
                tmdb_id: btn.dataset.tmdbId,
                title: btn.dataset.title,
                image: btn.dataset.image,
                release_date: btn.dataset.releaseDate,
                runtime: btn.dataset.runtime,
                category: btn.dataset.category
            };
            
            // Vérifier si le bouton est en mode "retirer" (déjà dans la liste)
            const isRemove = btn.classList.contains('js-watchlist-remove');
            const isCardBtn = btn.classList.contains('movie-card-add-btn');
            
            if (isRemove) {
                // Retirer de la liste
                fetch('/watchlist/remove', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(movieData)
                })
                .then(r => r.status === 401 ? (window.location.href = "/auth/login") : r.json())
                .then(d => {
                    if (d && d.success) {
                        if (isCardBtn) {
                            // Pour les boutons sur les cartes
                            btn.classList.remove('added', 'js-watchlist-remove');
                            btn.querySelector('i').className = 'fa fa-plus';
                        } else {
                            // Pour les boutons sur la page de détail
                            btn.innerHTML = '<i class="fa fa-plus" aria-hidden="true"></i> Ma Liste';
                            btn.classList.remove('js-watchlist-remove');
                            btn.style.opacity = '1';
                            btn.style.cursor = 'pointer';
                        }
                    } else {
                        alert("Erreur: " + (d.message || "Impossible de retirer"));
                    }
                })
                .catch(err => {
                    console.error('Erreur lors de la suppression:', err);
                    alert("Erreur lors de la suppression du film");
                });
            } else {
                // Ajouter à la liste
                fetch('/watchlist/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(movieData)
                })
                .then(r => r.status === 401 ? (window.location.href = "/auth/login") : r.json())
                .then(d => {
                    if (d && d.success) {
                        if (isCardBtn) {
                            // Pour les boutons sur les cartes
                            btn.classList.add('added', 'js-watchlist-remove');
                            btn.querySelector('i').className = 'fa fa-check';
                        } else {
                            // Pour les boutons sur la page de détail
                            btn.innerHTML = '<i class="fa fa-check" aria-hidden="true"></i> Dans ma liste';
                            btn.classList.add('js-watchlist-remove');
                            btn.style.opacity = '1';
                            btn.style.cursor = 'pointer';
                        }
                    } else {
                        alert("Erreur: " + (d.message || "Impossible d'ajouter"));
                    }
                })
                .catch(err => {
                    console.error('Erreur lors de l\'ajout:', err);
                    alert("Erreur lors de l'ajout du film");
                });
            }
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
                // Noter un film le marque automatiquement comme vu (géré côté serveur)

                fetch('/watchlist/rate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(movieData)
                })
                .then(r => r.status === 401 ? (window.location.href = "/auth/login") : r.json())
                .then(d => {
                    if (d && d.success) {
                        currentRating = newRating;
                        updateStarDisplay(starContainers, allStars, currentRating, false);
                        if (ratingValue) ratingValue.textContent = currentRating;
                        if (ratingLabel) ratingLabel.textContent = ratingLabels[currentRating] || '';
                        
                        // Marquer comme vu automatiquement si noté (le film est maintenant marqué comme vu)
                        if (watchedBtn) {
                            watchedBtn.classList.add('watched');
                            watchedBtn.dataset.watched = "true";
                            watchedBtn.querySelector('i').className = 'fa fa-check-circle';
                            watchedBtn.querySelector('.watched-text').textContent = 'Vu';
                        }
                        
                        // Mettre à jour le bouton "Ma Liste" pour qu'il affiche "Dans ma liste"
                        // (noter un film l'ajoute automatiquement à la watchlist)
                        const watchlistBtn = document.querySelector('.js-watchlist-btn:not(.movie-card-add-btn)');
                        if (watchlistBtn && !watchlistBtn.classList.contains('js-watchlist-remove')) {
                            watchlistBtn.innerHTML = '<i class="fa fa-check" aria-hidden="true"></i> Dans ma liste';
                            watchlistBtn.classList.add('js-watchlist-remove');
                            watchlistBtn.style.opacity = '1';
                            watchlistBtn.style.cursor = 'pointer';
                        }
                        
                        // Mettre à jour les boutons sur les cartes de films si présents
                        const cardBtns = document.querySelectorAll('.movie-card-add-btn[data-tmdb-id="' + movieData.tmdb_id + '"]');
                        cardBtns.forEach(btn => {
                            if (!btn.classList.contains('added')) {
                                btn.classList.add('added', 'js-watchlist-remove');
                                btn.querySelector('i').className = 'fa fa-check';
                            }
                        });
                        
                        // Si on est sur la page watchlist, recharger la liste pour mettre à jour les sections
                        if (typeof loadFilteredWatchlist === 'function') {
                            setTimeout(() => {
                                loadFilteredWatchlist();
                            }, 300);
                        }
                    }
                });
            });
        });
    }

    // --- 4. GESTION DE LA CRITIQUE ---
    const reviewTextarea = document.getElementById('review-textarea');
    const saveReviewBtn = document.getElementById('save-review-btn');
    const clearReviewBtn = document.getElementById('clear-review-btn');
    const reviewStatus = document.getElementById('review-status');

    if (saveReviewBtn && reviewTextarea) {
        saveReviewBtn.addEventListener('click', function() {
            const reviewText = reviewTextarea.value.trim();
            const movieData = getMovieDataFromPage();
            if (!movieData) return;

            movieData.review = reviewText;

            fetch('/watchlist/review', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(movieData)
            })
            .then(r => r.status === 401 ? (window.location.href = "/auth/login") : r.json())
            .then(d => {
                if (d && d.success) {
                    reviewStatus.textContent = 'Critique publiée avec succès !';
                    reviewStatus.className = 'review-status review-status-success';
                    setTimeout(() => {
                        reviewStatus.textContent = '';
                        reviewStatus.className = 'review-status';
                    }, 3000);
                    
                    // Afficher le bouton supprimer si la critique n'est pas vide
                    if (reviewText && !clearReviewBtn) {
                        // Le bouton sera ajouté dynamiquement si nécessaire
                        location.reload(); // Recharger pour afficher le bouton supprimer
                    }
                } else {
                    reviewStatus.textContent = 'Erreur lors de la publication';
                    reviewStatus.className = 'review-status review-status-error';
                    setTimeout(() => {
                        reviewStatus.textContent = '';
                        reviewStatus.className = 'review-status';
                    }, 3000);
                }
            })
            .catch(err => {
                console.error('Erreur lors de la sauvegarde:', err);
                reviewStatus.textContent = 'Erreur lors de la publication';
                reviewStatus.className = 'review-status review-status-error';
                setTimeout(() => {
                    reviewStatus.textContent = '';
                    reviewStatus.className = 'review-status';
                }, 3000);
            });
        });
    }

    if (clearReviewBtn) {
        clearReviewBtn.addEventListener('click', function() {
            if (confirm('Êtes-vous sûr de vouloir supprimer votre critique ?')) {
                const movieData = getMovieDataFromPage();
                if (!movieData) return;

                movieData.review = '';

                fetch('/watchlist/review', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(movieData)
                })
                .then(r => r.status === 401 ? (window.location.href = "/auth/login") : r.json())
                .then(d => {
                    if (d && d.success) {
                        reviewTextarea.value = '';
                        reviewStatus.textContent = 'Critique supprimée';
                        reviewStatus.className = 'review-status review-status-success';
                        setTimeout(() => {
                            reviewStatus.textContent = '';
                            reviewStatus.className = 'review-status';
                            location.reload(); // Recharger pour masquer le bouton supprimer
                        }, 1500);
                    } else {
                        reviewStatus.textContent = 'Erreur lors de la suppression';
                        reviewStatus.className = 'review-status review-status-error';
                        setTimeout(() => {
                            reviewStatus.textContent = '';
                            reviewStatus.className = 'review-status';
                        }, 3000);
                    }
                })
                .catch(err => {
                    console.error('Erreur lors de la suppression:', err);
                    reviewStatus.textContent = 'Erreur lors de la suppression';
                    reviewStatus.className = 'review-status review-status-error';
                    setTimeout(() => {
                        reviewStatus.textContent = '';
                        reviewStatus.className = 'review-status';
                    }, 3000);
                });
            }
        });
    }
});