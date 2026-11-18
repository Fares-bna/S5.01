// Liste des commandes slash, envoyée à Discord par scripts/enregistrer-commandes.js.
// Pour ajouter une commande : la déclarer ici, puis écrire sa fonction dans commandes.js.

const T = { SOUS_COMMANDE: 1, TEXTE: 3, ENTIER: 4, BOOLEEN: 5, UTILISATEUR: 6, SALON: 7 };
const GERER_SERVEUR = '32'; // permission "Gérer le serveur" (admins)

const choixStatut = [
  { name: 'À faire', value: 'a_faire' }, { name: 'En cours', value: 'en_cours' }, { name: 'Terminé', value: 'termine' }
];
const choixType = [
  { name: 'Tâche', value: 'tache' }, { name: 'Jalon interne', value: 'jalon' }, { name: 'Rendu prof', value: 'rendu' }
];
const id = { type: T.ENTIER, name: 'id', description: 'Numéro de la tâche (#12)', required: true };

export const COMMANDES = [
  {
    name: 'tache',
    description: 'Gérer les tâches et deadlines',
    options: [
      {
        type: T.SOUS_COMMANDE, name: 'ajouter', description: 'Ajouter une tâche',
        options: [
          { type: T.TEXTE, name: 'titre', description: 'Nom de la tâche', required: true },
          { type: T.TEXTE, name: 'fin', description: 'Date de fin (JJ/MM ou JJ/MM/AAAA)', required: true },
          { type: T.UTILISATEUR, name: 'responsable', description: 'Responsable (vide pour un jalon commun)' },
          { type: T.UTILISATEUR, name: 'partenaire', description: 'Partenaire' },
          { type: T.TEXTE, name: 'debut', description: 'Date de début (JJ/MM)' },
          { type: T.TEXTE, name: 'description', description: 'Détails, livrable attendu…' },
          { type: T.TEXTE, name: 'type', description: 'Tâche, jalon interne ou rendu prof', choices: choixType },
          { type: T.ENTIER, name: 'etape', description: 'Étape du projet (1 à 4)' }
        ]
      },
      {
        type: T.SOUS_COMMANDE, name: 'liste', description: 'Voir les tâches',
        options: [
          { type: T.UTILISATEUR, name: 'membre', description: 'Seulement les tâches de cette personne' },
          { type: T.TEXTE, name: 'statut', description: 'Filtrer par statut', choices: choixStatut },
          { type: T.ENTIER, name: 'etape', description: 'Filtrer par étape' },
          { type: T.BOOLEEN, name: 'tout', description: 'Inclure les tâches terminées' }
        ]
      },
      { type: T.SOUS_COMMANDE, name: 'voir', description: 'Détail d\'une tâche', options: [id] },
      {
        type: T.SOUS_COMMANDE, name: 'modifier', description: 'Modifier une tâche (seulement les champs remplis)',
        options: [
          id,
          { type: T.TEXTE, name: 'titre', description: 'Nouveau titre' },
          { type: T.TEXTE, name: 'fin', description: 'Nouvelle date de fin (JJ/MM)' },
          { type: T.TEXTE, name: 'debut', description: 'Nouvelle date de début (JJ/MM)' },
          { type: T.UTILISATEUR, name: 'responsable', description: 'Nouveau responsable' },
          { type: T.UTILISATEUR, name: 'partenaire', description: 'Nouveau partenaire' },
          { type: T.TEXTE, name: 'description', description: 'Nouvelle description' },
          { type: T.TEXTE, name: 'type', description: 'Nouveau type', choices: choixType },
          { type: T.ENTIER, name: 'etape', description: 'Nouvelle étape' }
        ]
      },
      {
        type: T.SOUS_COMMANDE, name: 'statut', description: 'Changer le statut (à faire, en cours, terminé)',
        options: [id, { type: T.TEXTE, name: 'statut', description: 'Nouveau statut', required: true, choices: choixStatut }]
      },
      { type: T.SOUS_COMMANDE, name: 'terminer', description: 'Confirmer qu\'une tâche est terminée (responsable ou admin)', options: [id] },
      { type: T.SOUS_COMMANDE, name: 'supprimer', description: 'Supprimer une tâche', options: [id] }
    ]
  },
  {
    name: 'membre',
    description: 'Associer les prénoms aux comptes Discord',
    options: [
      {
        type: T.SOUS_COMMANDE, name: 'lier', description: 'Associer un prénom à un compte Discord',
        options: [
          { type: T.TEXTE, name: 'prenom', description: 'Prénom utilisé dans les tâches', required: true },
          { type: T.UTILISATEUR, name: 'compte', description: 'Compte Discord', required: true }
        ]
      },
      { type: T.SOUS_COMMANDE, name: 'liste', description: 'Voir les membres et leurs comptes' }
    ]
  },
  {
    name: 'config',
    description: 'Régler le bot (admins)',
    default_member_permissions: GERER_SERVEUR,
    options: [
      { type: T.SOUS_COMMANDE, name: 'voir', description: 'Voir les réglages actuels' },
      {
        type: T.SOUS_COMMANDE, name: 'heure', description: 'Heure du récap quotidien',
        options: [{ type: T.TEXTE, name: 'heure', description: 'Format HH:MM, ex : 08:00', required: true }]
      },
      {
        type: T.SOUS_COMMANDE, name: 'salon', description: 'Salon où poster le récap',
        options: [{ type: T.SALON, name: 'salon', description: 'Salon', required: true, channel_types: [0] }]
      },
      {
        type: T.SOUS_COMMANDE, name: 'rappel', description: 'Activer ou couper un type de rappel',
        options: [
          {
            type: T.TEXTE, name: 'type', description: 'Type de rappel', required: true,
            choices: [
              { name: 'Commence aujourd\'hui', value: 'rappel_debut' },
              { name: 'Fin dans 3 jours (J-3)', value: 'rappel_j3' },
              { name: 'À rendre demain', value: 'rappel_veille' },
              { name: 'À rendre aujourd\'hui', value: 'rappel_jour' },
              { name: 'En retard', value: 'rappel_retard' },
              { name: 'Jalon / rendu dans 7 jours', value: 'rappel_jalon_j7' },
              { name: 'Jalon / rendu demain', value: 'rappel_jalon_j1' },
              { name: 'Récap de la semaine (lundi)', value: 'recap_hebdo' }
            ]
          },
          { type: T.BOOLEEN, name: 'actif', description: 'Oui pour activer, non pour couper', required: true }
        ]
      }
    ]
  },
  {
    name: 'recap',
    description: 'Récap des tâches pas encore terminées (déjà commencées ou en retard)',
    options: [
      { type: T.UTILISATEUR, name: 'membre', description: 'Seulement les tâches de cette personne' },
      { type: T.BOOLEEN, name: 'prive', description: 'Oui : visible seulement par toi (personne n\'est notifié). Par défaut : tout le monde' }
    ]
  },
  {
    name: 'rappel',
    description: 'Envoyer le récap du jour tout de suite (pour tester)',
    default_member_permissions: GERER_SERVEUR
  },
  {
    name: 'message',
    description: 'Faire parler le bot dans ce salon',
    default_member_permissions: GERER_SERVEUR,
    options: [{ type: T.TEXTE, name: 'texte', description: 'Ce que le bot doit dire', required: true }]
  },
  {
    name: 'aide',
    description: 'Comment utiliser le bot'
  }
];
