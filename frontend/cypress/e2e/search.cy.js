// frontend/cypress/e2e/search.cy.js

describe('SSOAR Search Flow', () => {
  beforeEach(() => {
    // 1) Visit the app
    cy.visit('http://localhost:5173');

    // 2) Wait for the search bar to appear by its Bootstrap class
    cy.get('input.form-control', { timeout: 10000 })
      .should('be.visible');
  });

  it('performs a search and displays results', () => {
    // Type and submit
    cy.get('input.form-control').clear().type('germany');
    cy.get('button').contains('Search').click();

    // Wait for at least one result card to appear
    cy.get('.card', { timeout: 10000 })
      .should('have.length.greaterThan', 0);
  });

  it('opens and closes the document modal', () => {
    // Trigger a search
    cy.get('input.form-control').clear().type('germany');
    cy.get('button').contains('Search').click();

    // Click the first title
    cy.get('.card-title').first().should('be.visible').click();

    // Modal opens
    cy.get('.modal', { timeout: 10000 }).should('be.visible');

    // Close it
    cy.get('.btn-close').click();
    cy.get('.modal').should('not.exist');
  });

  it('handles no-hit searches gracefully', () => {
    // Search for nonsense
    cy.get('input.form-control').clear().type('qwertyxyz');
    cy.get('button').contains('Search').click();

    // Expect the “no results” message
    cy.contains('No results found.', { timeout: 10000 })
      .should('be.visible');
  });
});