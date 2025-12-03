import { check, sleep } from 'k6';
import { ApiClient } from './utils/api-client.js';

export const options = {
  vus: 1,
  duration: '1m',
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const client = new ApiClient();

  // Health check
  const healthResult = client.healthCheck();
  check(healthResult.response, {
    'health check': (r) => r.status === 200,
  });

  // Create travel plan
  const createResult = client.createTravelPlan();
  check(createResult.response, {
    'create travel plan': (r) => r.status === 201,
  });

  if (createResult.travelPlanId) {
    // Get travel plan
    const getResult = client.getTravelPlan(createResult.travelPlanId);
    check(getResult.response, {
      'get travel plan': (r) => r.status === 200,
    });

    // List travel plans
    const listResult = client.listTravelPlans();
    check(listResult.response, {
      'list travel plans': (r) => r.status === 200,
    });

    // Create location
    const locationResult = client.createLocation(createResult.travelPlanId);
    check(locationResult.response, {
      'create location': (r) => r.status === 201,
    });

    // List locations
    const locationsListResult = client.listLocations();
    check(locationsListResult.response, {
      'list locations': (r) => r.status === 200,
    });
  }

  sleep(1);
}

