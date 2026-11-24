'use server';
import {backend} from '../../../../lib/backend';
const root = (id: string) => `/api/businesses/${encodeURIComponent(id)}/distributed-runs`;
export async function readRuns(id: string) {
  return backend(root(id));
}
export async function runCommand(id: string, command: string, payload: Record<string, unknown> = {}, runId = '') {
  let path = root(id);
  if (command === 'cancel' || command === 'proposal') path += `/${encodeURIComponent(runId)}/${command}`;
  else if (command !== 'submit') throw new Error('Unknown simulation command');
  return backend(path, {method: 'POST', body: JSON.stringify(payload)});
}
