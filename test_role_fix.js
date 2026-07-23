// Test script to verify the role fix works correctly

// Mock data that could cause the original error
const testUsers = [
  {
    id: '1',
    name: 'Test User 1',
    roles: [{ id: 1, name: 'Role 1' }, { id: 2, name: 'Role 2' }] // Normal case
  },
  {
    id: '2',
    name: 'Test User 2',
    roles: [] // Empty roles array
  },
  {
    id: '3',
    name: 'Test User 3',
    roles: [null, { id: 3, name: 'Role 3' }, undefined] // Mixed with null/undefined
  },
  {
    id: '4',
    name: 'Test User 4',
    roles: [{ name: 'Role Without ID' }, { id: 4, name: 'Role 4' }] // Role without id
  },
  {
    id: '5',
    name: 'Test User 5'
    // No roles property at all
  }
];

// Test the original problematic code
function testOriginalCode(user) {
  try {
    const existingRoleIds = (user?.roles || []).map(r => r.id);
    console.log(`Original code - User ${user.id}:`, existingRoleIds);
    return existingRoleIds;
  } catch (error) {
    console.log(`Original code - User ${user.id} ERROR:`, error.message);
    return null;
  }
}

// Test the fixed code
function testFixedCode(user) {
  try {
    const existingRoleIds = (user?.roles || []).filter(r => r?.id).map(r => r.id);
    console.log(`Fixed code - User ${user.id}:`, existingRoleIds);
    return existingRoleIds;
  } catch (error) {
    console.log(`Fixed code - User ${user.id} ERROR:`, error.message);
    return null;
  }
}

console.log('=== Testing Original vs Fixed Code ===');
testUsers.forEach(user => {
  console.log(`\nTesting user ${user.id}: ${user.name}`);
  testOriginalCode(user);
  testFixedCode(user);
});

console.log('\n=== Testing Select Value Generation ===');

// Test the Select component value generation
function testOriginalSelectValue(user) {
  try {
    const value = (user.roles || []).map(r => ({ value: r.id, label: r.name }));
    console.log(`Original Select - User ${user.id}:`, value);
    return value;
  } catch (error) {
    console.log(`Original Select - User ${user.id} ERROR:`, error.message);
    return null;
  }
}

function testFixedSelectValue(user) {
  try {
    const value = (user.roles || []).filter(r => r?.id && r?.name).map(r => ({ value: r.id, label: r.name }));
    console.log(`Fixed Select - User ${user.id}:`, value);
    return value;
  } catch (error) {
    console.log(`Fixed Select - User ${user.id} ERROR:`, error.message);
    return null;
  }
}

testUsers.forEach(user => {
  console.log(`\nTesting Select value for user ${user.id}: ${user.name}`);
  testOriginalSelectValue(user);
  testFixedSelectValue(user);
});
