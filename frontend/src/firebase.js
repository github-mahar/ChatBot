// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyD-tNzUgRUOUx9BuucZWjR7qckJ3775muI",
  authDomain: "ai-chatbot-97a78.firebaseapp.com",
  projectId: "ai-chatbot-97a78",
  storageBucket: "ai-chatbot-97a78.firebasestorage.app",
  messagingSenderId: "272103220325",
  appId: "1:272103220325:web:8d19bf70a921a1a84d928c",
  measurementId: "G-NYSN7MW5DY"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

export { app, analytics, firebaseConfig };
