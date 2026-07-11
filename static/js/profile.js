/**
 * Profile Image & Data Sync (FIXED VERSION)
 * Syncs profile data across all pages without glitches
 */

// Central profile data store
const profileData = {
  userId: 'alex-rivera',
  name: 'Alex Rivera',
  role: 'Talent Lead',
  email: 'alex.rivera@lumina.example.com',
  imageUrl: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAlz_tIYSUQaLdZo-aSkiLpj-UmQ7QLoWulGJhQnqqBXcerHR4e65c3lSSuZirDOsALEZOHbZ5WTMqkjMq6oToqwVMYx581IHGSOLrhnXJvcYUHCMNhRz579JFwiZXu6B1AL0on-F10yOVJp3XvdGTKAqJkPELDMETAI7Kxv3v4iKMy9E6db-ycaUf9t97NfWR9mjToxZbJ-huLhEWVbsFO3D2VZx9MuGlyKQPCQctwcVwre4ZWw4F_m0klb0Lx-T8yo4zI0hDmhwsi'
};

// Load profile from localStorage
function loadProfileFromStorage() {
  try {
    const stored = localStorage.getItem('lumina_profile_data');
    if (stored) {
      const parsed = JSON.parse(stored);
      profileData.name = parsed.name || profileData.name;
      profileData.role = parsed.role || profileData.role;
      profileData.email = parsed.email || profileData.email;
      profileData.imageUrl = parsed.imageUrl || profileData.imageUrl;
    }
  } catch (e) {
    console.error('Error loading profile from storage:', e);
  }
}

// Save profile to localStorage
function saveProfileToStorage() {
  try {
    localStorage.setItem('lumina_profile_data', JSON.stringify({
      name: profileData.name,
      role: profileData.role,
      email: profileData.email,
      imageUrl: profileData.imageUrl
    }));
  } catch (e) {
    console.error('Error saving profile to storage:', e);
  }
}

// Sync all profile images across pages
function syncAllImages() {
  const url = profileData.imageUrl;
  
  // Navbar profile image
  const navbarImg = document.querySelector('.user-chip img');
  if (navbarImg) {
    navbarImg.src = url;
    navbarImg.onerror = () => console.warn('Navbar image failed to load');
  }
  
  // Profile page hero avatar
  const heroImg = document.querySelector('.pf-avatar');
  if (heroImg) {
    heroImg.src = url;
    heroImg.onerror = () => console.warn('Hero image failed to load');
  }
  
  // Settings preview image
  const previewImg = document.getElementById('profile-preview');
  if (previewImg) {
    previewImg.src = url;
    previewImg.onerror = () => console.warn('Preview image failed to load');
  }
  
  // Any element with data-profile-image attribute
  document.querySelectorAll('[data-profile-image]').forEach(img => {
    img.src = url;
  });
}

// Sync all profile text data
function syncAllText() {
  // Update navbar user chip
  const navbarName = document.querySelector('.user-chip-name');
  const navbarRole = document.querySelector('.user-chip-role');
  
  if (navbarName) navbarName.textContent = profileData.name;
  if (navbarRole) navbarRole.textContent = profileData.role;
  
  // Update profile page hero
  const heroName = document.querySelector('.pf-hero-info h2');
  if (heroName) heroName.textContent = profileData.name;
  
  // Update settings form inputs
  const nameInput = document.getElementById('name-input');
  const roleInput = document.getElementById('role-input');
  const emailInput = document.getElementById('email-input');
  
  if (nameInput) nameInput.value = profileData.name;
  if (roleInput) roleInput.value = profileData.role;
  if (emailInput) emailInput.value = profileData.email;
  
  // Update info rows
  document.querySelectorAll('.pf-info-row').forEach(row => {
    const key = row.querySelector('span.k');
    const value = row.querySelector('span.v');
    
    if (key && value) {
      if (key.textContent.includes('Email')) {
        value.textContent = profileData.email;
      }
    }
  });
}

// Update profile image (with validation)
function updateProfileImage(newImageUrl) {
  if (!newImageUrl || typeof newImageUrl !== 'string') {
    console.error('Invalid image URL');
    return;
  }
  
  profileData.imageUrl = newImageUrl;
  saveProfileToStorage();
  syncAllImages();
  console.log('✓ Profile image updated');
}

// Update profile data (name, role, email)
function updateProfileData(updates) {
  if (!updates || typeof updates !== 'object') {
    console.error('Invalid update object');
    return;
  }
  
  // Only update known fields
  if (updates.name) profileData.name = updates.name;
  if (updates.role) profileData.role = updates.role;
  if (updates.email) profileData.email = updates.email;
  
  saveProfileToStorage();
  syncAllText();
  console.log('✓ Profile data updated');
}

// Handle image upload from file input
function handleImageUpload(fileInput) {
  if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
    console.warn('No file selected');
    return;
  }
  
  const file = fileInput.files[0];
  
  // Validate file type
  if (!file.type.startsWith('image/')) {
    alert('Please upload an image file (JPG, PNG, etc.)');
    fileInput.value = ''; // Reset input
    return;
  }
  
  // Validate file size (max 5MB)
  const maxSize = 5 * 1024 * 1024; // 5MB
  if (file.size > maxSize) {
    alert('File size must be less than 5MB');
    fileInput.value = ''; // Reset input
    return;
  }
  
  // Read and convert to data URL
  const reader = new FileReader();
  
  reader.onload = (e) => {
    try {
      const dataUrl = e.target.result;
      updateProfileImage(dataUrl);
      console.log('✓ Image uploaded successfully');
    } catch (error) {
      console.error('Error processing image:', error);
      alert('Error uploading image. Please try again.');
    }
  };
  
  reader.onerror = () => {
    console.error('Error reading file');
    alert('Error reading file. Please try again.');
    fileInput.value = ''; // Reset input
  };
  
  reader.readAsDataURL(file);
}

// Initialize profile on page load
function initializeProfile() {
  loadProfileFromStorage();
  
  // Wait for DOM to be fully loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      syncAllImages();
      syncAllText();
    });
  } else {
    syncAllImages();
    syncAllText();
  }
}

// Expose functions globally
window.profileSync = {
  updateProfileImage,
  updateProfileData,
  handleImageUpload,
  getProfile: () => ({ ...profileData }),
  syncAll: () => {
    syncAllImages();
    syncAllText();
  }
};

// Auto-initialize
initializeProfile();