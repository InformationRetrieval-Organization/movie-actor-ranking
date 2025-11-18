import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardBody, Link, Pagination, Image } from "@heroui/react";

// Utility function to format the IMDb ID
const formatImdbId = (imdbId: number): string => {
    return `nm${imdbId.toString().padStart(7, '0')}`;
};

const formatImdbActorUrl = (imdbId: number): string => {
    return `https://www.imdb.com/name/${formatImdbId(imdbId)}`;
}

export default function ResultsList({ results }: { results: ActorModel[] }) {
    const [currentPage, setCurrentPage] = useState(1);
    const [searchPerformed, setSearchPerformed] = useState(false);
    const [initialRender, setInitialRender] = useState(true);
    const resultsPerPage = 10;

    // Calculate the range of results for the current page
    const startIndex = (currentPage - 1) * resultsPerPage;
    const endIndex = startIndex + resultsPerPage;
    const resultsForPage = results.slice(startIndex, endIndex);

    // On the initial render, it sets initialRender to false.
    // On subsequent renders (when results change), it sets searchPerformed to true.
    useEffect(() => {
        if (initialRender) {
            setInitialRender(false);
        } else {
            setSearchPerformed(true);
        }
    }, [results]);

    // If the search was performed and no results were found, display a message
    if (searchPerformed && results.length === 0) {
        return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Nothing found</div>
    }

    return (
        <div>
            {resultsForPage.map((result, index) => (
                <Card key={index} className="mt-3">
                    <CardBody>
                        <div className="flex gap-6 items-center justify-center">
                            <div className="">
                                <Image
                                    alt={result.headshotUrl ? `${result.name}'s profile` : "No profile picture available"}
                                    height={100}
                                    width={100}
                                    className="object-cover"
                                    shadow="md"
                                    src={result.headshotUrl ? result.headshotUrl : "https://corporate.bestbuy.com/wp-content/uploads/2022/06/Image-Portrait-Placeholder.jpg"}
                                />
                            </div>
                            <div className="flex flex-col grow">
                                <div className="flex flex-col col-span-6">
                                    <Link className="mb-3 text-4xl" href={formatImdbActorUrl(result.imdbId)} target="_blank">{result.name}</Link>
                                    {result.roles.slice(0, 3).map((role, i) => (
                                        <div key={i} className="flex flex-col gap-2">
                                            <p className="text-sm"><em>{role.name}</em> in <strong>{role.movie.title}</strong></p>
                                        </div>
                                    ))}
                                    {result.roles.length > 3 && <p className="text-sm">...</p>}
                                </div>
                            </div>
                        </div>
                    </CardBody>
                </Card>
            ))}
            <Pagination
                className="mt-3"
                total={Math.ceil(results.length / resultsPerPage)}
                initialPage={1}
                onChange={(page) => setCurrentPage(page)}
            />
        </div>
    );
}