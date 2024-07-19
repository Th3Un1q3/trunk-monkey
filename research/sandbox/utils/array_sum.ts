import {add} from "./add";

export function array_sum(array: number[]): number {
  return array.reduce(add, 0)
}