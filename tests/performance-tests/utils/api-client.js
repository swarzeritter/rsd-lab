import http from 'k6/http';
import { check } from 'k6';
import { endpoints } from '../config/endpoints.js';
import { generateTravelPlan, generateLocation } from './data-generator.js';

export class ApiClient {
  constructor(baseUrl = endpoints.baseUrl) {
    this.baseUrl = baseUrl;
    this.params = {
      headers: {
        'Content-Type': 'application/json',
      },
    };
  }

  healthCheck() {
    const url = `${this.baseUrl}${endpoints.health}`;
    const response = http.get(url, this.params);
    return {
      success: check(response, {
        'health check status is 200': (r) => r.status === 200,
      }),
      response,
    };
  }

  createTravelPlan() {
    const url = `${this.baseUrl}${endpoints.travelPlans.create}`;
    const payload = JSON.stringify(generateTravelPlan());
    const response = http.post(url, payload, this.params);
    
    const success = check(response, {
      'create travel plan status is 201': (r) => r.status === 201,
      'create travel plan has id': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.id !== undefined;
        } catch {
          return false;
        }
      },
    });
    
    let travelPlanId = null;
    if (success) {
      try {
        const body = JSON.parse(response.body);
        travelPlanId = body.id;
      } catch (e) {
        // Ignore parse error
      }
    }
    
    return { success, response, travelPlanId };
  }

  getTravelPlan(id) {
    const url = `${this.baseUrl}${endpoints.travelPlans.getById(id)}`;
    const response = http.get(url, this.params);
    return {
      success: check(response, {
        'get travel plan status is 200': (r) => r.status === 200,
      }),
      response,
    };
  }

  listTravelPlans(skip = 0, limit = 10) {
    const url = `${this.baseUrl}${endpoints.travelPlans.list}?skip=${skip}&limit=${limit}`;
    const response = http.get(url, this.params);
    return {
      success: check(response, {
        'list travel plans status is 200': (r) => r.status === 200,
        'list travel plans returns array': (r) => {
          try {
            const body = JSON.parse(r.body);
            return Array.isArray(body);
          } catch {
            return false;
          }
        },
      }),
      response,
    };
  }

  updateTravelPlan(id, version = 1) {
    const url = `${this.baseUrl}${endpoints.travelPlans.update(id)}`;
    const payload = JSON.stringify({
      ...generateTravelPlan(),
      version: version,
    });
    const response = http.put(url, payload, this.params);
    return {
      success: check(response, {
        'update travel plan status is 200': (r) => r.status === 200,
      }),
      response,
    };
  }

  deleteTravelPlan(id) {
    const url = `${this.baseUrl}${endpoints.travelPlans.delete(id)}`;
    const response = http.del(url, null, this.params);
    return {
      success: check(response, {
        'delete travel plan status is 200': (r) => r.status === 200,
      }),
      response,
    };
  }

  createLocation(travelPlanId) {
    const url = `${this.baseUrl}${endpoints.travelPlans.addLocation(travelPlanId)}`;
    const locationData = generateLocation(travelPlanId);
    // Remove travel_plan_id from payload as it comes from URL
    delete locationData.travel_plan_id;
    const payload = JSON.stringify(locationData);
    const response = http.post(url, payload, this.params);
    
    return {
      success: check(response, {
        'create location status is 201': (r) => r.status === 201,
      }),
      response,
    };
  }

  listLocations(skip = 0, limit = 10) {
    const url = `${this.baseUrl}${endpoints.locations.list}?skip=${skip}&limit=${limit}`;
    const response = http.get(url, this.params);
    return {
      success: check(response, {
        'list locations status is 200': (r) => r.status === 200,
      }),
      response,
    };
  }
}

