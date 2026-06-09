/* AppFirebase — simple global wrapper for Firebase auth (compat SDK used) */
window.AppFirebase = (function(){
  let app = null;
  let auth = null;

  function init(config){
    app = firebase.initializeApp(config);
    auth = firebase.auth();
  }

  function signInWithGoogle(){
    const provider = new firebase.auth.GoogleAuthProvider();
    return auth.signInWithPopup(provider);
  }

  function signOut(){
    return auth.signOut();
  }

  function onAuthStateChanged(cb){
    if(!auth) return;
    auth.onAuthStateChanged(cb);
  }

  function currentUser(){
    return auth ? auth.currentUser : null;
  }

  return { init, signInWithGoogle, signOut, onAuthStateChanged, currentUser };
})();
