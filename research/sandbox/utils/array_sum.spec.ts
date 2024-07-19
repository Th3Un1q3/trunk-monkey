import { array_sum } from './array_sum';

describe('array_sum', () => {
  it('should return 0 for an empty array', () => {
    expect(array_sum([])).toBe(0);
  });
  it('should return the sum of the elements of the array', () => {
    expect(array_sum([1, 2, 3])).toBe(6);
  });
});