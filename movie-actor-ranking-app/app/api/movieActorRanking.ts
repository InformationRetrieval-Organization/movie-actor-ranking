"use server";
const baseUrl = process.env.MAR_API_URL;

type RawActor = Partial<ActorModel> & {
    roles?: RoleModel[];
};

const normalizeActor = (actor: RawActor): ActorModel => {
    return {
        id: actor.id ?? 0,
        imdbId: actor.imdbId ?? 0,
        name: actor.name ?? "Unknown",
        headshotUrl: actor.headshotUrl ?? "",
        roles: Array.isArray(actor.roles) ? actor.roles : [],
    };
};

export async function getActors(query: string): Promise<ActorModel[]> {  
    try {
        console.log(`fetch actors with: ${baseUrl}/search/classifier/actor?q=${encodeURIComponent(query)}`);

        const response = await fetch(`${baseUrl}/search/classifier/actor?q=${encodeURIComponent(query)}`);

        const data = await response.json();
        const actors: ActorModel[] = Array.isArray(data)
            ? data.map((actor) => normalizeActor(actor as RawActor))
            : [];

        return actors;
    } catch (error) {
        console.error(`Error fetching actors: ${error}`);
        return [];
    }
}
