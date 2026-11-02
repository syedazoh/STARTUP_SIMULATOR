import test from 'node:test'
import assert from 'node:assert/strict'
import { resolveMessage, getLatestMessage } from '../src/components/boardroom/eventRoutes.js'

test('routes marketing budget request to finance without inventing message data', () => {
  const event = { event_id:'e1', source:'marketing', event_type:'budget_request', data:{amount:500} }
  assert.deepEqual(resolveMessage(event), { id:'e1',sender:'marketing',receiver:'finance',type:'budget_request' })
})

test('routes finance arbitration requests to CEO', () => {
  assert.equal(resolveMessage({event_id:'e2', source:'finance',event_type:'arbitration_request',data:{}}).receiver,'ceo')
})

test('ignores externally published or unknown events', () => {
  assert.equal(resolveMessage({event_id:'e3', source:'api',event_type:'campaign_launch',data:{}}),null)
  assert.equal(resolveMessage({event_id:'e4', source:'system',event_type:'kpi_updated',data:{}}),null)
})

test('accepts explicit sender and receiver on structured events', () => {
  assert.deepEqual(resolveMessage({event_id:'e5',sender:'hr',receiver:'ceo',event_type:'agent.message'}),{id:'e5',sender:'hr',receiver:'ceo',type:'agent.message'})
})

test('latest event is not assumed to be a conversation', () => {
  const events = [
    {event_id:'e1',source:'marketing',event_type:'budget_request',data:{}},
    {event_id:'e2',source:'system',event_type:'kpi_updated',data:{}},
  ]
  assert.equal(getLatestMessage(events).id,'e1')
})
