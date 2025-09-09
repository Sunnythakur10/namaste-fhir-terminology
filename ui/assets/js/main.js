/**
 * NAMASTE-FHIR Terminology Bridge - Main JavaScript
 * 
 * This file provides core functionality for the NAMASTE-FHIR terminology translation UI
 * including autocomplete, API interactions, and UI utilities.
 */

// Configuration and Constants
const CONFIG = {
  // API endpoint constants (would connect to actual backend in production)
  API_ENDPOINTS: {
    SEARCH: '/api/search',
    TRANSLATE: '/api/translate',
    AUTOCOMPLETE: '/api/autocomplete',
    FHIR_UPLOAD: '/api/fhir-upload',
    ANALYTICS: '/api/analytics',
    PREVALENCE: '/api/prevalence',
    POLICY_CHECK: '/api/policy-check',
    VALUE_SET: '/api/valueSet/$expand'
  },
  // Default options
  DEFAULTS: {
    AUTOCOMPLETE_DELAY: 300,
    RESULT_LIMIT: 10,
    DATE_FORMAT: 'YYYY-MM-DD'
  },
  // Mock authentication for demo purposes
  AUTH: {
    TOKEN: 'mock-abha-token',
    TOKEN_TYPE: 'Bearer'
  }
};

/**
 * Enhanced Autocomplete for Terminology Search
 * 
 * Provides real-time suggestions as users type, with dual-coding support
 * showing both NAMASTE and ICD-11 codes.
 */
class TerminologyAutocomplete {
  /**
   * Create a new autocomplete instance
   * 
   * @param {HTMLElement} inputElement - The input field for search
   * @param {Object} options - Configuration options
   */
  constructor(inputElement, options = {}) {
    // Elements
    this.inputElement = inputElement;
    this.containerId = options.containerId || inputElement.id + '-autocomplete';
    this.resultsContainer = document.getElementById(this.containerId);
    
    if (!this.resultsContainer) {
      // Create container if it doesn't exist
      this.resultsContainer = document.createElement('div');
      this.resultsContainer.id = this.containerId;
      this.resultsContainer.className = 'autocomplete-items';
      this.resultsContainer.style.display = 'none';
      inputElement.parentNode.appendChild(this.resultsContainer);
    }
    
    // State
    this.debounceTimeout = null;
    this.selectedTerm = null;
    this.currentFocus = -1;
    this.results = [];
    
    // Options
    this.minChars = options.minChars || 2;
    this.delay = options.delay || CONFIG.DEFAULTS.AUTOCOMPLETE_DELAY;
    this.limit = options.limit || CONFIG.DEFAULTS.RESULT_LIMIT;
    this.onSelect = options.onSelect || null;
    this.mockMode = options.mockMode || true;
    this.mockData = options.mockData || this._getMockTerminology();
    
    // Initialize
    this._setupEventListeners();
  }
  
  /**
   * Set up event listeners for the autocomplete
   * @private
   */
  _setupEventListeners() {
    // Input events for searching
    this.inputElement.addEventListener('input', () => {
      clearTimeout(this.debounceTimeout);
      this.debounceTimeout = setTimeout(() => this._performSearch(), this.delay);
    });
    
    // Handle keyboard navigation
    this.inputElement.addEventListener('keydown', (e) => this._handleKeyDown(e));
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
      if (e.target !== this.inputElement && e.target !== this.resultsContainer) {
        this._closeDropdown();
      }
    });
  }
        this.fetchSuggestions();
      }, 300);
    });
    
    document.addEventListener('click', (e) => {
      if (!this.inputElement.contains(e.target) && 
          !this.resultsContainer.contains(e.target)) {
        this.clearResults();
      }
    });
  }
  
  /**
   * Perform search and display results
   * @private
   */
  _performSearch: function() {
    const query = this.inputElement.value.trim();
    
    if (query.length < this.minChars) {
      this._closeDropdown();
      return;
    }
    
    if (this.mockMode) {
      // For demo, use mock data
      this._searchMockData(query);
    } else {
      // In production, this would call the actual API
      this._searchAPI(query);
    }
  },
  
  /**
   * Search within mock data (for demo purposes)
   * @private
   * @param {string} query - The search query
   */
  _searchMockData: function(query) {
    const lowercaseQuery = query.toLowerCase();
    const results = this.mockData.filter(item => {
      return item.term.toLowerCase().includes(lowercaseQuery) ||
             (item.namasteCode && item.namasteCode.toLowerCase().includes(lowercaseQuery)) ||
             (item.icdCode && item.icdCode.toLowerCase().includes(lowercaseQuery));
    }).slice(0, this.limit);
    
    this._displayResults(results);
  },
  
  displayResults(results) {
    this.clearResults();
    
    if (!results || results.length === 0) {
      const noResults = document.createElement('div');
      noResults.className = 'autocomplete-item';
      noResults.textContent = 'No results found';
      this.resultsContainer.appendChild(noResults);
      return;
    }
    
    results.forEach(item => {
      const resultItem = document.createElement('div');
      resultItem.className = 'autocomplete-item';
      
      // Create HTML content for the result item
      resultItem.innerHTML = `
        <div class="term-name">${item.term}</div>
        <div class="term-codes">
          <span class="code-badge namaste-badge">${item.namasteCode || 'N/A'}</span>
          <span class="code-badge icd-badge">${item.icdCode || 'N/A'}</span>
        </div>
      `;
      
      resultItem.addEventListener('click', () => {
        this.selectTerm(item);
      });
      
      this.resultsContainer.appendChild(resultItem);
    });
  }
  
  selectTerm(term) {
    this.selectedTerm = term;
    this.inputElement.value = term.term;
    this.clearResults();
    
    // Dispatch event for other components to react
    const event = new CustomEvent('term-selected', { detail: term });
    document.dispatchEvent(event);
  }
  
  clearResults() {
    this.resultsContainer.innerHTML = '';
  }
}

/**
 * Problem List Manager
 */
class ProblemListManager {
  constructor(containerElement) {
    this.containerElement = containerElement;
    this.problemList = [];
    
    this.init();
  }
  
  init() {
    document.addEventListener('term-selected', (e) => {
      this.addProblem(e.detail);
    });
  }
  
  addProblem(term) {
    if (!term) return;
    
    // Check if already in the list
    const existingIndex = this.problemList.findIndex(p => 
      p.namasteCode === term.namasteCode || p.icdCode === term.icdCode
    );
    
    if (existingIndex >= 0) {
      // Update existing problem
      this.problemList[existingIndex] = term;
    } else {
      // Add new problem
      this.problemList.push(term);
    }
    
    this.renderProblemList();
  }
  
  removeProblem(index) {
    this.problemList.splice(index, 1);
    this.renderProblemList();
  }
  
  renderProblemList() {
    this.containerElement.innerHTML = '';
    
    if (this.problemList.length === 0) {
      const emptyMessage = document.createElement('div');
      emptyMessage.className = 'empty-list-message';
      emptyMessage.textContent = 'No problems added yet';
      this.containerElement.appendChild(emptyMessage);
      return;
    }
    
    this.problemList.forEach((problem, index) => {
      const problemItem = document.createElement('div');
      problemItem.className = 'dual-code';
      
      problemItem.innerHTML = `
        <div class="problem-info">
          <div class="problem-term">${problem.term}</div>
          <div class="problem-codes">
            <span class="code-badge namaste-badge">${problem.namasteCode || 'N/A'}</span>
            <span class="code-badge icd-badge">${problem.icdCode || 'N/A'}</span>
          </div>
        </div>
        <button class="btn-remove" data-index="${index}">Remove</button>
      `;
      
      const removeButton = problemItem.querySelector('.btn-remove');
      removeButton.addEventListener('click', () => {
        this.removeProblem(index);
      });
      
      this.containerElement.appendChild(problemItem);
    });
  }
  
  getFHIRBundle() {
    // Create a FHIR bundle with the problems
    const bundle = {
      resourceType: "Bundle",
      type: "collection",
      entry: this.problemList.map(problem => ({
        resource: {
          resourceType: "Condition",
          code: {
            coding: [
              {
                system: "http://ayush.gov.in/namaste",
                code: problem.namasteCode,
                display: problem.term
              },
              {
                system: "http://id.who.int/icd11/mms",
                code: problem.icdCode,
                display: problem.term
              }
            ],
            text: problem.term
          },
          subject: {
            reference: "Patient/example"
          },
          recordedDate: new Date().toISOString().split('T')[0]
        }
      }))
    };
    
    return bundle;
  }
}

// Initialize components when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Setup autocomplete
  const searchInput = document.getElementById('diagnosis-search');
  const resultsContainer = document.getElementById('search-results');
  
  if (searchInput && resultsContainer) {
    new TerminologyAutocomplete(searchInput, resultsContainer);
  }
  
  // Setup problem list
  const problemListContainer = document.getElementById('problem-list');
  
  if (problemListContainer) {
    const problemListManager = new ProblemListManager(problemListContainer);
    
    // Setup export button
    const exportButton = document.getElementById('export-fhir');
    if (exportButton) {
      exportButton.addEventListener('click', () => {
        const bundle = problemListManager.getFHIRBundle();
        
        // For demo, just show the bundle in console or alert
        console.log('FHIR Bundle:', bundle);
        
        // Could also send to the server
        // fetch(API_ENDPOINTS.FHIR_UPLOAD, {
        //   method: 'POST',
        //   headers: {
        //     'Authorization': `Bearer ${MOCK_AUTH_TOKEN}`,
        //     'Content-Type': 'application/json'
        //   },
        //   body: JSON.stringify(bundle)
        // });
      });
    }
  }
});
