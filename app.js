// Book Management System

// Initialize books array with sample data including book with ID 1
let books = [
  { id: 1, title: "The Great Gatsby", author: "F. Scott Fitzgerald" },
  { id: 2, title: "To Kill a Mockingbird", author: "Harper Lee" },
  { id: 3, title: "1984", author: "George Orwell" },
  { id: 4, title: "Pride and Prejudice", author: "Jane Austen" },
  { id: 5, title: "The Catcher in the Rye", author: "J.D. Salinger" },
  { id: 6, title: "Brave New World", author: "Aldous Huxley" },
  { id: 7, title: "The Hobbit", author: "J.R.R. Tolkien" },
  { id: 8, title: "Moby Dick", author: "Herman Melville" }
];

let nextId = 9;
let currentSearchTerm = '';

// DOM Elements
const booksGrid = document.getElementById('booksGrid');
const emptyState = document.getElementById('emptyState');
const searchInput = document.getElementById('searchInput');
const addBookForm = document.getElementById('addBookForm');
const addForm = document.getElementById('addForm');
const showAddFormBtn = document.getElementById('showAddFormBtn');
const cancelAddBtn = document.getElementById('cancelAddBtn');
const updateBookForm = document.getElementById('updateBookForm');
const updateForm = document.getElementById('updateForm');
const showUpdateFormBtn = document.getElementById('showUpdateFormBtn');
const cancelUpdateBtn = document.getElementById('cancelUpdateBtn');
const deleteHighestIdBtn = document.getElementById('deleteHighestIdBtn');

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
  loadBooksFromStorage();
  renderBooks();
  setupEventListeners();
});

// Load books from localStorage
function loadBooksFromStorage() {
  const savedBooks = localStorage.getItem('books');
  if (savedBooks) {
    const parsed = JSON.parse(savedBooks);
    // Only use saved books if they exist and have data
    if (parsed && parsed.length > 0) {
      books = parsed;
      // Calculate next ID
      nextId = Math.max(...books.map(b => b.id)) + 1;
    }
  }
  // If no saved books or empty, use the default books array already initialized
}

// Save books to localStorage
function saveBooksToStorage() {
  localStorage.setItem('books', JSON.stringify(books));
}

// Setup event listeners
function setupEventListeners() {
  // Search functionality
  searchInput.addEventListener('input', (e) => {
    currentSearchTerm = e.target.value.toLowerCase().trim();
    renderBooks();
  });

  // Show add form
  showAddFormBtn.addEventListener('click', () => {
    addBookForm.classList.remove('hidden');
    addBookForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
    document.getElementById('addTitle').focus();
  });

  // Cancel add form
  cancelAddBtn.addEventListener('click', () => {
    addBookForm.classList.add('hidden');
    addForm.reset();
  });

  // Add book form submission
  addForm.addEventListener('submit', (e) => {
    e.preventDefault();
    addBook();
  });

  // Show update form
  showUpdateFormBtn.addEventListener('click', () => {
    updateBookForm.classList.remove('hidden');
    updateBookForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
    document.getElementById('updateId').focus();
  });

  // Cancel update form
  cancelUpdateBtn.addEventListener('click', () => {
    updateBookForm.classList.add('hidden');
    updateForm.reset();
  });

  // Update book form submission
  updateForm.addEventListener('submit', (e) => {
    e.preventDefault();
    updateBook();
  });

  // Delete highest ID book
  deleteHighestIdBtn.addEventListener('click', () => {
    deleteHighestIdBook();
  });
}

// Feature 1: Add new book
function addBook() {
  const title = document.getElementById('addTitle').value.trim();
  const author = document.getElementById('addAuthor').value.trim();

  if (!title || !author) {
    alert('Please fill in all fields');
    return;
  }

  const newBook = {
    id: nextId++,
    title: title,
    author: author
  };

  books.push(newBook);
  saveBooksToStorage();

  // Reset form and hide
  addForm.reset();
  addBookForm.classList.add('hidden');

  // Clear search and redirect to home view
  currentSearchTerm = '';
  searchInput.value = '';

  // Render updated books list
  renderBooks();

  // Scroll to top to show updated list
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Feature 2: Update book with user-provided ID, title, and author
function updateBook() {
  const bookId = parseInt(document.getElementById('updateId').value.trim());
  const newTitle = document.getElementById('updateTitle').value.trim();
  const newAuthor = document.getElementById('updateAuthor').value.trim();

  if (!bookId || !newTitle || !newAuthor) {
    alert('Please fill in all fields');
    return;
  }

  const bookIndex = books.findIndex(book => book.id === bookId);

  if (bookIndex === -1) {
    alert(`Book with ID ${bookId} not found!`);
    return;
  }

  // Update the book
  books[bookIndex].title = newTitle;
  books[bookIndex].author = newAuthor;

  saveBooksToStorage();

  // Reset form and hide
  updateForm.reset();
  updateBookForm.classList.add('hidden');

  // Clear search and redirect to home view
  currentSearchTerm = '';
  searchInput.value = '';

  // Render updated books list
  renderBooks();

  // Scroll to top
  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Visual feedback
  setTimeout(() => {
    const updatedCard = document.querySelector(`[data-book-id="${bookId}"]`);
    if (updatedCard) {
      updatedCard.style.animation = 'none';
      setTimeout(() => {
        updatedCard.style.animation = 'scaleIn 0.4s ease';
      }, 10);
    }
  }, 100);
}

// Feature 3: Delete book with highest ID
function deleteHighestIdBook() {
  if (books.length === 0) {
    alert('No books to delete!');
    return;
  }

  // Find the book with the highest ID
  const highestId = Math.max(...books.map(book => book.id));
  const bookToDelete = books.find(book => book.id === highestId);

  if (confirm(`Delete "${bookToDelete.title}" by ${bookToDelete.author}?`)) {
    // Remove the book
    books = books.filter(book => book.id !== highestId);
    saveBooksToStorage();

    // Clear search and redirect to home view
    currentSearchTerm = '';
    searchInput.value = '';

    // Render updated books list
    renderBooks();

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

// Feature 4: Search functionality - filter books by title or author
function getFilteredBooks() {
  if (!currentSearchTerm) {
    return books;
  }

  return books.filter(book =>
    book.title.toLowerCase().includes(currentSearchTerm) ||
    book.author.toLowerCase().includes(currentSearchTerm)
  );
}

// Render books to the DOM
function renderBooks() {
  const filteredBooks = getFilteredBooks();

  // Clear current display
  booksGrid.innerHTML = '';

  // Show/hide empty state
  if (filteredBooks.length === 0) {
    emptyState.classList.remove('hidden');
    booksGrid.classList.add('hidden');

    if (currentSearchTerm) {
      emptyState.innerHTML = `
        <div class="empty-state-icon">🔍</div>
        <p>No books found matching "${currentSearchTerm}"</p>
      `;
    } else {
      emptyState.innerHTML = `
        <div class="empty-state-icon">📖</div>
        <p>No books found. Add your first book to get started!</p>
      `;
    }
    return;
  }

  emptyState.classList.add('hidden');
  booksGrid.classList.remove('hidden');

  // Render each book
  filteredBooks.forEach((book, index) => {
    const bookCard = createBookCard(book, index);
    booksGrid.appendChild(bookCard);
  });
}

// Create a book card element
function createBookCard(book, index) {
  const card = document.createElement('div');
  card.className = 'book-card';
  card.setAttribute('data-book-id', book.id);
  card.style.animationDelay = `${index * 0.1}s`;

  card.innerHTML = `
    <div class="book-id">ID: ${book.id}</div>
    <h3 class="book-title">${escapeHtml(book.title)}</h3>
    <p class="book-author">${escapeHtml(book.author)}</p>
  `;

  return card;
}

// Utility function to escape HTML
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
