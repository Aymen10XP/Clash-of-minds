describe('game menu navigation', () => {
  beforeEach(() => {
    cy.visit('/home');
  });

  it('moves through VS Bot and returns to the menu', () => {
    cy.contains('.menu-button', 'VS Bot').click();
    cy.location('pathname').should('equal', '/practice');
    cy.contains('h2', 'How will you challenge the archive?').should('be.visible');

    cy.get('[aria-label="Go back"]').click();
    cy.location('pathname').should('equal', '/home');
    cy.contains('.menu-button', 'VS Bot').should('be.visible');
  });

  it('moves through Multiplayer and its ranked placeholder', () => {
    cy.contains('.menu-button', 'Multiplayer').click();
    cy.location('pathname').should('equal', '/multiplayer');
    cy.contains('button', 'Ranked Matchmaking').click();
    cy.location('pathname').should('equal', '/multiplayer/ranked');
    cy.contains('h1', 'Ranked Matchmaking').should('be.visible');

    cy.get('[aria-label="Go back"]').click();
    cy.location('pathname').should('equal', '/multiplayer');
    cy.contains('button', 'Friendly Match').should('be.visible');
  });
});
