# Guide de dépannage Vercel - Erreur 404

## 🔍 Problèmes courants et solutions

### 1. Erreur 404 après déploiement

**Causes possibles :**
- Les fichiers `vercel.json` ou `api/index.py` ne sont pas correctement configurés
- Les imports Python ne fonctionnent pas
- Les variables d'environnement ne sont pas définies
- La base de données n'est pas accessible

**Solutions :**

#### A. Vérifier les fichiers de configuration

Assurez-vous que ces fichiers existent :
- ✅ `vercel.json` à la racine
- ✅ `api/index.py` dans le dossier `api/`
- ✅ `api/__init__.py` (fichier vide)

#### B. Vérifier les logs de déploiement

1. Allez sur [vercel.com/dashboard](https://vercel.com/dashboard)
2. Sélectionnez votre projet
3. Cliquez sur **"Deployments"**
4. Cliquez sur le dernier déploiement
5. Regardez les **"Build Logs"** et **"Function Logs"**

#### C. Vérifier les variables d'environnement

Dans le dashboard Vercel, section **"Settings"** → **"Environment Variables"**, assurez-vous d'avoir :

| Variable | Obligatoire | Exemple |
|----------|-------------|---------|
| `SECRET_KEY` | ✅ Oui | `a1b2c3d4e5f6...` |
| `DATABASE_URL` | ✅ Oui | `postgresql://user:pass@host:5432/db` |
| `API_key` | ✅ Oui | Votre clé TMDB v3 |
| `JetonTMDB` | ✅ Oui | Votre jeton TMDB v4 |
| `FLASK_DEBUG` | ⚠️ Recommandé | `False` |

**⚠️ Important :**
- Pas de guillemets autour des valeurs
- Respecter la casse exacte
- Redéployer après avoir ajouté/modifié des variables

#### D. Tester localement avec Vercel CLI

```bash
# Installer Vercel CLI
npm i -g vercel

# Tester localement
vercel dev
```

### 2. Erreur "Module not found"

**Solution :**
- Vérifiez que `requirements.txt` contient toutes les dépendances
- Vérifiez les logs de build pour voir quel module manque

### 3. Erreur de connexion à la base de données

**Solution :**
- Vérifiez que `DATABASE_URL` est correcte
- Vérifiez que votre base PostgreSQL accepte les connexions externes
- Testez la connexion avec un client PostgreSQL

### 4. Les fichiers statiques ne se chargent pas

**Solution :**
- Vérifiez que le dossier `static/` est bien dans le repository
- Vérifiez que les chemins dans les templates utilisent `url_for('static', ...)`

### 5. L'application fonctionne mais certaines routes ne marchent pas

**Solution :**
- Vérifiez que tous les blueprints sont bien enregistrés dans `app.py`
- Vérifiez les logs de fonction pour voir les erreurs spécifiques

## 📝 Checklist de déploiement

Avant de redéployer, vérifiez :

- [ ] `vercel.json` existe et est correct
- [ ] `api/index.py` existe et exporte `application`
- [ ] `api/__init__.py` existe (fichier vide)
- [ ] Toutes les variables d'environnement sont définies dans Vercel
- [ ] `requirements.txt` contient toutes les dépendances
- [ ] La base de données PostgreSQL est accessible depuis Internet
- [ ] Les fichiers `static/` et `templates/` sont dans le repository

## 🔄 Redéploiement

Après avoir corrigé les problèmes :

1. Commitez les changements :
   ```bash
   git add .
   git commit -m "Fix Vercel configuration"
   git push
   ```

2. Vercel redéploiera automatiquement, ou :
   - Allez sur le dashboard Vercel
   - Cliquez sur **"Redeploy"** sur le dernier déploiement

## 🆘 Si ça ne marche toujours pas

1. **Vérifiez les logs** dans le dashboard Vercel
2. **Testez avec Vercel CLI** : `vercel dev`
3. **Vérifiez la documentation** : [vercel.com/docs](https://vercel.com/docs)
4. **Contactez le support Vercel** si nécessaire

## 📚 Ressources

- [Documentation Vercel Python](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)
- [Documentation Flask sur Vercel](https://vercel.com/guides/deploying-flask-with-vercel)

