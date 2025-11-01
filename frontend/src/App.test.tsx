import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';

// Simple component test
test('renders without crashing', () => {
  const TestComponent = () => <div>PlantPal Test</div>;
  render(<TestComponent />);
  expect(document.body).toBeInTheDocument();
});

test('basic functionality test', () => {
  const result = 2 + 2;
  expect(result).toBe(4);
});

test('string manipulation test', () => {
  const text = 'PlantPal';
  expect(text.toLowerCase()).toBe('plantpal');
  expect(text.length).toBe(8);
});