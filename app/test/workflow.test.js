import test from 'node:test';
import assert from 'node:assert/strict';
import { applyCommand, canJoin, government, createInitialData, spacesLeft } from '../src/js/workflow.js';
import { createWorkflowStore, STORAGE_KEY } from '../src/js/workflow-store.js';
import { escapeHtml } from '../src/js/format.js';

const now = Date.parse('2026-09-21T10:00:00Z');
const initial = () => createInitialData(now);
const activist = (data, index = 0) => data.profiles[index];
const submit = (data, actor, type, payload) => applyCommand(data, actor, { type, payload }, now);
const reportInput = { title: 'Oil near the quay', place: 'Dordrecht quay', category: 'Water pollution', urgency: 'urgent', observedAt: new Date(now - 1000).toISOString(), note: 'An oily sheen is visible near the outlet.', evidence: 'https://example.org/photo.jpg' };
const callInput = { title: 'Survey the quay', place: 'Harbour entrance', description: 'Meet the field lead and record affected areas.', when: new Date(now + 86400000).toISOString(), help: 'survey', capacity: 1 };

function memoryStorage() {
  const entries = new Map();
  return { getItem: (key) => entries.get(key) ?? null, setItem: (key, value) => entries.set(key, value) };
}

test('report → government response → linked call → signup → completion → resolution', () => {
  let data = initial();
  const person = activist(data);
  const report = submit(data, person, 'submitReport', reportInput);
  data = report.data;
  assert.equal(report.result.authorId, person.id);
  assert.equal(report.result.status, 'new');
  data = submit(data, government, 'respondToReport', { id: report.result.id, status: 'reviewing', body: 'A field lead is checking this report.' }).data;
  const call = submit(data, government, 'publishCall', { ...callInput, reportId: report.result.id });
  data = call.data;
  assert.equal(data.reports[0].status, 'action_required');
  assert.equal(data.reports[0].responses.length, 2);
  data = submit(data, person, 'joinCall', { id: call.result.id }).data;
  assert.equal(spacesLeft(data.calls[0]), 0);
  assert.equal(canJoin(data.calls[0], now), false);
  data = submit(data, government, 'updateCall', { id: call.result.id, status: 'completed', body: 'Site survey completed.' }).data;
  assert.equal(data.reports[0].status, 'action_required', 'Finishing a call must not silently resolve a violation');
  data = submit(data, government, 'respondToReport', { id: report.result.id, status: 'resolved', body: 'Discharge stopped and water retested.' }).data;
  assert.equal(data.reports[0].responses.length, 3);
  assert.equal(data.reports[0].status, 'resolved');
  assert.equal(data.calls[0].participants[0], person.id);
  assert.equal(data.activity[0].targetId, report.result.id);
});

test('signups enforce capacity, reject duplicates, and release a withdrawn spot', () => {
  let data = initial();
  const call = submit(data, government, 'publishCall', callInput);
  const id = call.result.id;
  data = submit(call.data, activist(data), 'joinCall', { id }).data;
  assert.throws(() => submit(data, activist(data), 'joinCall', { id }), /already joined/);
  assert.throws(() => submit(data, activist(data, 1), 'joinCall', { id }), /no longer accepting/);
  data = submit(data, activist(data), 'withdrawCall', { id }).data;
  assert.equal(spacesLeft(data.calls[0]), 1);
  data = submit(data, activist(data, 1), 'joinCall', { id }).data;
  assert.deepEqual(data.calls[0].participants, [activist(data, 1).id]);
});

test('roles protect publishing, responses, signups, and violation submission', () => {
  const data = initial();
  assert.throws(() => submit(data, activist(data), 'publishCall', callInput), /not available/);
  assert.throws(() => submit(data, activist(data), 'respondToReport', { id: 'r1', status: 'resolved', body: 'Done' }), /not available/);
  assert.throws(() => submit(data, government, 'submitReport', reportInput), /not available/);
  assert.throws(() => submit(data, government, 'joinCall', { id: 'wetlands' }), /not available/);
  assert.throws(() => submit(data, { role: 'people', id: 'unknown' }, 'joinCall', { id: 'wetlands' }), /not available/);
});

test('invalid reports do not mutate data or accept unsafe evidence', () => {
  const data = initial();
  const original = structuredClone(data);
  for (const input of [ { title: '  ' }, { urgency: 'invalid' }, { observedAt: new Date(now + 1000).toISOString() }, { evidence: 'javascript:alert(1)' }, { evidence: 'data:text/html,<script>' }, { note: 'x'.repeat(4001) } ]) {
    assert.throws(() => submit(data, activist(data), 'submitReport', { ...reportInput, ...input }));
  }
  assert.deepEqual(data, original);
  assert.equal(escapeHtml('<img src=x onerror="alert(1)">'), '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;');
});

test('invalid dates, fractional capacity, and terminal report links are rejected', () => {
  const data = initial();
  for (const input of [ { when: 'invalid' }, { when: new Date(now).toISOString() }, { capacity: 0 }, { capacity: 1.5 }, { capacity: 1001 }, { reportId: 'missing' }, { reportId: 'r4' } ]) {
    assert.throws(() => submit(data, government, 'publishCall', { ...callInput, ...input }));
  }
});

test('closed and past calls reject signups; completed calls are immutable', () => {
  let data = initial();
  data = submit(data, government, 'updateCall', { id: 'wetlands', status: 'closed', body: 'The crew is ready.' }).data;
  assert.throws(() => submit(data, activist(data, 2), 'joinCall', { id: 'wetlands' }), /no longer accepting/);
  data = submit(data, government, 'updateCall', { id: 'wetlands', status: 'open', body: 'One extra spot needed.' }).data;
  assert.equal(canJoin(data.calls[0], now), true);
  data.calls[0].when = new Date(now - 1000).toISOString();
  assert.throws(() => submit(data, activist(data, 2), 'joinCall', { id: 'wetlands' }), /no longer accepting/);
  assert.throws(() => submit(data, activist(data), 'withdrawCall', { id: 'wetlands' }), /ended/);
  assert.throws(() => submit(data, government, 'updateCall', { id: 'wetlands', status: 'open', body: 'Please join.' }), /past/);
  data = submit(data, government, 'updateCall', { id: 'wetlands', status: 'completed', body: 'Survey finished.' }).data;
  assert.throws(() => submit(data, government, 'updateCall', { id: 'wetlands', status: 'open', body: 'Reopen.' }), /ended/);
});

test('resolved or dismissed violations must explicitly reopen with a response', () => {
  const data = initial();
  assert.throws(() => submit(data, government, 'respondToReport', { id: 'r4', status: 'action_required', body: 'Needs action.' }), /Reopen/);
  assert.throws(() => submit(data, government, 'respondToReport', { id: 'r4', status: 'reviewing', body: ' ' }), /Response is required/);
  const reopened = submit(data, government, 'respondToReport', { id: 'r4', status: 'reviewing', body: 'New evidence received.' });
  assert.equal(reopened.result.status, 'reviewing');
  assert.equal(reopened.result.responses.length, 2);
});

test('returning profiles retain their identity and own records', () => {
  const data = initial();
  const profile = submit(data, null, 'saveProfile', { name: ' alex MORGAN ', place: 'Utrecht', help: 'restore' });
  assert.equal(profile.result.id, 'am');
  assert.equal(profile.data.profiles.length, data.profiles.length);
  assert.ok(profile.data.calls[0].participants.includes(profile.result.id));
  const other = submit(profile.data, null, 'saveProfile', { name: 'New Activist', place: 'Ghent', help: 'survey' });
  assert.notEqual(other.result.id, 'am');
  assert.equal(other.data.reports.filter((report) => report.authorId === other.result.id).length, 0);
});

test('reloads and independent tabs preserve reports, responses, and signups', () => {
  const storage = memoryStorage();
  const tabA = createWorkflowStore(storage, () => now);
  const tabB = createWorkflowStore(storage, () => now);
  const report = tabA.dispatch(activist(tabA.data), { type: 'submitReport', payload: reportInput });
  tabB.dispatch(government, { type: 'respondToReport', payload: { id: report.id, status: 'reviewing', body: 'Received in another tab.' } });
  const call = tabA.dispatch(government, { type: 'publishCall', payload: callInput });
  tabB.dispatch(activist(tabB.data), { type: 'joinCall', payload: { id: call.id } });
  const reload = createWorkflowStore(storage, () => now);
  assert.equal(reload.data.reports[0].responses[0].body, 'Received in another tab.');
  assert.equal(reload.data.calls[0].participants.length, 1);
  assert.throws(() => tabA.dispatch(activist(tabA.data, 1), { type: 'joinCall', payload: { id: call.id } }), /no longer accepting/);
});

test('failed persistence keeps existing records and reports an actionable error', () => {
  const storage = memoryStorage();
  const store = createWorkflowStore(storage, () => now);
  const original = structuredClone(store.data);
  storage.setItem = () => { throw new Error('Quota exceeded'); };
  assert.throws(() => store.dispatch(activist(store.data), { type: 'submitReport', payload: reportInput }), /could not be saved/);
  assert.deepEqual(store.data, original);
  const broken = createWorkflowStore({ getItem: () => '{broken', setItem() { assert.fail('Must not overwrite corrupt data'); } }, () => now);
  assert.ok(broken.error);
  assert.throws(() => broken.dispatch(government, { type: 'publishCall', payload: callInput }), /could not be read/);
  assert.ok(storage.getItem(STORAGE_KEY));
});
