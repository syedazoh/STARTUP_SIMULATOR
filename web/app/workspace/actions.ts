"use server";
import { backend } from "../../lib/backend";
import { businessPayload, workforcePayload } from "../../lib/workspace-contracts";
export async function createBusiness(form: FormData) {
  try {
    const business = await backend("/api/businesses", {
      method: "POST",
      body: JSON.stringify(businessPayload(form)),
    });
    return { ok: true as const, id: business.id as string };
  } catch (error) {
    return {
      ok: false as const,
      error:
        error instanceof Error ? error.message : "Could not create business.",
    };
  }
}

export async function saveWorkforce(businessId:string,form:FormData){try{const business=await backend(`/api/businesses/${encodeURIComponent(businessId)}/workforce`,{method:'PUT',body:JSON.stringify(workforcePayload(form))});return {ok:true as const,workforce:business.workforce}}catch(error){return {ok:false as const,error:error instanceof Error?error.message:'Team could not be saved.'}}}
