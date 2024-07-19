import {add} from "./add";

/**
 * Sums all the elements of an numerical array
 * @param array
 * @returns the sum of the elements of the array
 */
export function array_sum(array: number[]): number {
  return array.reduce(add, 0)
}