/**
 * Main JavaScript for NAMASTE-FHIR UI
 */

// API endpoint constants
const API_ENDPOINTS = {
  SEARCH: '/api/search',
  TRANSLATE: '/api/translate',
  AUTOCOMPLETE: '/api/autocomplete',
  FHIR_UPLOAD: '/api/fhir-upload',
  ANALYTICS: '/api/analytics'
};

// Mock token for demo purposes
const MOCK_AUTH_TOKEN = 'mock-abha-token';

/**
 * Autocomplete functionality for diagnosis search
 */
class TerminologyAutocomplete {
  constructor(inputElement, resultsContainer) {
    this.inputElement = inputElement;
    this.resultsContainer = resultsContainer;
    this.debounceTimeout = null;
    this.selectedTerm = null;
    
    this.init();
  }
  
  init() {
    this.inputElement.addEventListener('input', () => {
      clearTimeout(this.debounceTimeout);
      this.debounceTimeout = setTimeout(() => {
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
  
  async fetchSuggestions() {
    const searchTerm = this.inputElement.value.trim();
    if (searchTerm.length < 2) {
      this.clearResults();
      return;
    }
    
    try {
      const response = await fetch(`${API_ENDPOINTS.AUTOCOMPLETE}?term=${encodeURIComponent(searchTerm)}`, {
        headers: {
          'Authorization': `Bearer ${MOCK_AUTH_TOKEN}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch suggestions');
      }
      
      const data = await response.json();
      this.displayResults(data.results);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      this.clearResults();
    }
  }
  
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
