/// <reference types="cypress" />

/** Browser-level checks for navigation, accessible controls, auth errors, and mobile layout. */
describe('game menu navigation', () => {
  /** Gives signed-in screens a deterministic session and prevents test data from hitting the API. */
  beforeEach(() => {
    cy.intercept('GET', '/api/auth/me/', {
      statusCode: 200,
      body: {
        authenticated: true,
        user: {
          id: 1,
          username: 'e2e-player',
          email: 'e2e@example.com',
          country: 'TN',
          isStaff: false,
        },
      },
    });
    cy.intercept('GET', '/api/quiz/offline/catalog/', {
      statusCode: 401,
      body: { error: 'Sign in to download the offline question pack.' },
    });
    cy.visit('/home');
  });

  /** Verifies key home controls have usable accessible names. */
  it('exposes named navigation and account controls to assistive technology', () => {
    cy.get('[role="navigation"][aria-label="Game modes"]').should('be.visible');
    cy.get('ion-button.menu-button').first().shadow()
      .find('button[aria-label="Story Mode: Uncover the lost archives"]').should('be.visible');
    cy.get('ion-button.account-control').shadow()
      .find('button[aria-label="Log out e2e-player"]').should('be.visible');
  });

  it('moves through VS Bot and returns to the menu', () => {
    cy.contains('.menu-button', 'VS Bot').click();
    cy.location('pathname').should('equal', '/practice');
    cy.get('h1').should('contain.text', 'VS Bot');
    cy.get('.game-choice-card').should('have.length', 2);

    cy.contains('h1', 'VS Bot').closest('.ion-page')
      .find('ion-button.game-screen-header__back').click();
    cy.location('pathname').should('equal', '/home');
    cy.contains('.menu-button', 'VS Bot').should('be.visible');
  });

  it('moves through Multiplayer and its ranked placeholder', () => {
    cy.contains('.menu-button', 'Multiplayer').click();
    cy.location('pathname').should('equal', '/multiplayer');
    cy.get('.game-choice-card').contains('Ranked Matchmaking').click();
    cy.location('pathname').should('equal', '/multiplayer/ranked');
    cy.get('ion-router-outlet > .ion-page:not(.ion-page-hidden)', { timeout: 10000 })
      .contains('h1', 'Ranked Matchmaking').should('be.visible');

    cy.contains('h1', 'Ranked Matchmaking').closest('.ion-page')
      .find('ion-button.game-screen-header__back').click();
    cy.location('pathname').should('equal', '/multiplayer');
    cy.get('.game-choice-card').contains('Friendly Match').should('be.visible');
  });

  it('shows a labelled login form and announces rejected credentials', () => {
    cy.intercept('GET', '/api/auth/me/', {
      statusCode: 200,
      body: { authenticated: false, user: null },
    });
    cy.visit('/login');

    cy.get('ion-card.auth-panel form').should('be.visible');
    cy.get('ion-input.auth-input').should('have.length', 2);
    cy.get('ion-input.auth-input').eq(0).should('have.prop', 'label', 'Username or email');
    cy.get('ion-input.auth-input').eq(1).should('have.prop', 'label', 'Password');

    cy.intercept('POST', '/api/auth/login/', {
      statusCode: 400,
      body: { error: 'The username/email or password is incorrect.' },
    }).as('rejectedLogin');
    cy.setCookie('csrftoken', 'e2e-csrf-token');
    cy.get('ion-input.auth-input').eq(0).find('input').type('unknown-player');
    cy.get('ion-input.auth-input').eq(1).find('input').type('incorrect-password');
    cy.contains('ion-button', 'Sign in').click();
    cy.wait('@rejectedLogin');
    cy.get('[role="alert"]').should('contain.text', 'incorrect');
  });

  /** Checks for horizontal overflow at a common phone viewport size. */
  it('keeps the main navigation within a phone viewport', () => {
    cy.viewport('iphone-6');
    cy.get('[role="navigation"][aria-label="Game modes"]').should('be.visible');
    cy.get('body').then(($body) => {
      expect($body[0].scrollWidth).to.be.at.most($body[0].clientWidth);
    });
  });
});
